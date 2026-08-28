"""Persistência Supabase."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from supabase import Client, create_client

from acc_nomad.config import settings
from acc_nomad.models import BankCode, Transaction


class SupabaseNotConfiguredError(RuntimeError):
    pass


def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SupabaseNotConfiguredError(
            "Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY em backend/.env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def update_extrato_status(
    extrato_id: str,
    *,
    status: str,
    banco: BankCode | None = None,
    total_lancamentos: int | None = None,
    erro_mensagem: str | None = None,
) -> None:
    client = get_supabase_client()
    payload: dict[str, Any] = {"status": status}
    if banco is not None:
        payload["banco"] = banco.value
    if total_lancamentos is not None:
        payload["total_lancamentos"] = total_lancamentos
    if erro_mensagem is not None:
        payload["erro_mensagem"] = erro_mensagem
    if status == "processado":
        payload["processed_at"] = datetime.now(UTC).isoformat()

    client.table("extratos").update(payload).eq("id", extrato_id).execute()


def update_extrato_saldo_validation(
    extrato_id: str,
    *,
    saldo_inicial: float | None,
    saldo_final: float | None,
    saldo_calculado: float | None,
    validacao_saldo_ok: bool,
    validacao_detalhes: dict[str, Any],
) -> None:
    client = get_supabase_client()
    client.table("extratos").update(
        {
            "saldo_inicial": saldo_inicial,
            "saldo_final": saldo_final,
            "saldo_calculado": saldo_calculado,
            "validacao_saldo_ok": validacao_saldo_ok,
            "validacao_detalhes": validacao_detalhes,
        }
    ).eq("id", extrato_id).execute()


def save_transactions(
    extrato_id: str,
    empresa_id: str,
    transactions: list[Transaction],
) -> dict[str, Any]:
    client = get_supabase_client()
    rows = [
        {
            "extrato_id": extrato_id,
            "empresa_id": empresa_id,
            "data": tx.date.isoformat(),
            "descricao": tx.description,
            "valor": tx.amount,
            "natureza": tx.nature.value,
            "categoria": tx.category,
            "origem": tx.origin.value,
            "metadata": tx.metadata,
        }
        for tx in transactions
    ]

    result = client.table("lancamentos").insert(rows).execute()
    return {"saved": True, "count": len(rows), "result": result.data}


def fetch_fornecedores(empresa_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    result = (
        client.table("fornecedores")
        .select("nome, categoria_sugerida")
        .eq("empresa_id", empresa_id)
        .execute()
    )
    return result.data or []


def fetch_plano_contas(segmento: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    result = (
        client.table("plano_contas")
        .select("codigo, nome, categoria_pai, ordem")
        .eq("segmento", segmento or "comercio")
        .eq("ativo", True)
        .order("ordem")
        .execute()
    )
    return result.data or []

