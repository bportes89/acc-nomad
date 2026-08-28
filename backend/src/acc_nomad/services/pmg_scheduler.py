"""Disparo semanal automático do PMG."""

from __future__ import annotations

import calendar
from datetime import UTC, date, datetime, timedelta
from typing import Any

from acc_nomad.services.pmg_calculator import calcular_pmg_resumo, fetch_pmg_data
from acc_nomad.services.pmg_delivery import DeliveryError, enviar_pmg
from acc_nomad.services.supabase_client import get_supabase_client


def previous_month_period(reference: date | None = None) -> tuple[str, date, date]:
    ref = reference or date.today()
    if ref.month == 1:
        year, month = ref.year - 1, 12
    else:
        year, month = ref.year, ref.month - 1
    inicio = date(year, month, 1)
    fim = date(year, month, calendar.monthrange(year, month)[1])
    periodo = f"{year:04d}-{month:02d}"
    return periodo, inicio, fim


def fetch_active_agendamentos(dia_semana: int | None = None) -> list[dict[str, Any]]:
    client = get_supabase_client()
    query = client.table("pmg_agendamentos").select("*, empresas(nome)").eq("ativo", True)
    if dia_semana is not None:
        query = query.eq("dia_semana", dia_semana)
    result = query.execute()
    return result.data or []


def _already_sent_this_week(client, empresa_id: str, periodo: str, canal: str) -> bool:
    week_ago = (datetime.now(UTC) - timedelta(days=6)).isoformat()
    result = (
        client.table("envios_pmg")
        .select("id")
        .eq("empresa_id", empresa_id)
        .eq("canal", canal)
        .eq("status", "enviado")
        .gte("created_at", week_ago)
        .execute()
    )
    rows = result.data or []
    return len(rows) > 0


async def run_weekly_pmg_dispatch(
    *,
    force: bool = False,
    dia_semana: int | None = None,
) -> dict[str, Any]:
    today = date.today()
    weekday = dia_semana if dia_semana is not None else today.weekday()

    if force:
        agendamentos = fetch_active_agendamentos()
    else:
        agendamentos = fetch_active_agendamentos(dia_semana=weekday)

    periodo, inicio, fim = previous_month_period(today)
    client = get_supabase_client()

    enviados: list[dict[str, str]] = []
    erros: list[dict[str, str]] = []
    ignorados: list[dict[str, str]] = []

    for ag in agendamentos:
        empresa_id = ag["empresa_id"]
        canal = ag["canal"]
        destinatario = ag["destinatario"]
        empresa_nome = (ag.get("empresas") or {}).get("nome") or "Empresa"

        if not force and _already_sent_this_week(client, empresa_id, periodo, canal):
            ignorados.append(
                {
                    "empresa_id": empresa_id,
                    "motivo": "Já enviado nos últimos 7 dias",
                }
            )
            continue

        lancamentos, tesouraria = fetch_pmg_data(empresa_id, inicio, fim)
        resumo = calcular_pmg_resumo(lancamentos, tesouraria)

        if not lancamentos and not tesouraria:
            ignorados.append(
                {
                    "empresa_id": empresa_id,
                    "motivo": f"Sem lançamentos em {periodo}",
                }
            )
            continue

        try:
            await enviar_pmg(
                empresa_id=empresa_id,
                empresa_nome=empresa_nome,
                periodo=periodo,
                periodo_inicio=inicio,
                periodo_fim=fim,
                canal=canal,
                destinatario=destinatario,
                resumo=resumo,
                enviado_por=None,
            )
            client.table("pmg_agendamentos").update(
                {"ultimo_envio_em": datetime.now(UTC).isoformat()}
            ).eq("id", ag["id"]).execute()
            enviados.append(
                {
                    "empresa": empresa_nome,
                    "destinatario": destinatario,
                    "canal": canal,
                    "periodo": periodo,
                }
            )
        except DeliveryError as exc:
            erros.append(
                {
                    "empresa": empresa_nome,
                    "destinatario": destinatario,
                    "erro": str(exc),
                }
            )

    return {
        "periodo": periodo,
        "dia_semana": weekday,
        "total_agendamentos": len(agendamentos),
        "enviados": enviados,
        "erros": erros,
        "ignorados": ignorados,
    }
