"""Envio de relatório PMG por Email e WhatsApp."""

from __future__ import annotations

import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from acc_nomad.config import settings
from acc_nomad.services.supabase_client import get_supabase_client


class DeliveryError(RuntimeError):
    pass


def _format_pmg_text(resumo: dict[str, float], periodo: str, empresa: str) -> str:
    resultado = (
        resumo.get("receita", 0)
        - resumo.get("custo_variavel", 0)
        - resumo.get("custo_fixo", 0)
        - resumo.get("juros", 0)
        - resumo.get("investimentos", 0)
    )
    return f"""ACC Nomad — Relatório PMG
Empresa: {empresa}
Período: {periodo}

Receita:          R$ {resumo.get('receita', 0):,.2f}
Custo Variável:   R$ {resumo.get('custo_variavel', 0):,.2f}
Custo Fixo:       R$ {resumo.get('custo_fixo', 0):,.2f}
Juros:            R$ {resumo.get('juros', 0):,.2f}
Investimentos:    R$ {resumo.get('investimentos', 0):,.2f}
─────────────────────────
Resultado:        R$ {resultado:,.2f}

Gerado automaticamente pelo ACC Nomad.
"""


def send_email(destinatario: str, assunto: str, corpo: str) -> None:
    if not settings.smtp_host or not settings.email_from:
        raise DeliveryError(
            "SMTP não configurado. Defina SMTP_HOST, SMTP_USER, SMTP_PASSWORD e EMAIL_FROM em backend/.env"
        )

    msg = MIMEMultipart()
    msg["From"] = settings.email_from
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


def send_whatsapp(destinatario: str, mensagem: str) -> None:
    if not settings.whatsapp_api_url:
        raise DeliveryError(
            "WhatsApp não configurado. Defina WHATSAPP_API_URL e WHATSAPP_API_TOKEN em backend/.env"
        )

    headers = {"Content-Type": "application/json"}
    if settings.whatsapp_api_token:
        headers["Authorization"] = f"Bearer {settings.whatsapp_api_token}"

    payload = {
        "number": destinatario,
        "message": mensagem,
    }

    response = httpx.post(
        settings.whatsapp_api_url,
        json=payload,
        headers=headers,
        timeout=30,
    )
    if response.status_code >= 400:
        raise DeliveryError(f"WhatsApp API erro {response.status_code}: {response.text[:200]}")


def registrar_envio(
    *,
    empresa_id: str,
    periodo_inicio: date,
    periodo_fim: date,
    canal: str,
    destinatario: str,
    status: str,
    enviado_por: str | None = None,
    erro_mensagem: str | None = None,
) -> dict[str, Any]:
    client = get_supabase_client()
    row = {
        "empresa_id": empresa_id,
        "periodo_inicio": periodo_inicio.isoformat(),
        "periodo_fim": periodo_fim.isoformat(),
        "canal": canal,
        "destinatario": destinatario,
        "status": status,
        "enviado_por": enviado_por,
        "erro_mensagem": erro_mensagem,
    }
    result = client.table("envios_pmg").insert(row).execute()
    return {"saved": True, "data": result.data}


async def enviar_pmg(
    *,
    empresa_id: str,
    empresa_nome: str,
    periodo: str,
    periodo_inicio: date,
    periodo_fim: date,
    canal: str,
    destinatario: str,
    resumo: dict[str, float],
    enviado_por: str | None = None,
) -> dict[str, str]:
    corpo = _format_pmg_text(resumo, periodo, empresa_nome)
    assunto = f"ACC Nomad — PMG {periodo} — {empresa_nome}"

    try:
        if canal == "email":
            send_email(destinatario, assunto, corpo)
        elif canal == "whatsapp":
            send_whatsapp(destinatario, corpo)
        else:
            raise DeliveryError(f"Canal inválido: {canal}")

        registrar_envio(
            empresa_id=empresa_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            canal=canal,
            destinatario=destinatario,
            status="enviado",
            enviado_por=enviado_por,
        )
        return {"status": "enviado", "canal": canal, "destinatario": destinatario}
    except Exception as exc:
        registrar_envio(
            empresa_id=empresa_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            canal=canal,
            destinatario=destinatario,
            status="erro",
            enviado_por=enviado_por,
            erro_mensagem=str(exc),
        )
        raise DeliveryError(str(exc)) from exc
