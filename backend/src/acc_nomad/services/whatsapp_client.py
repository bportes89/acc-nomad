"""Cliente WhatsApp — Evolution API, Z-API ou payload genérico."""

from __future__ import annotations

import re
from typing import Any

import httpx

from acc_nomad.config import settings

Provider = str


class WhatsAppError(RuntimeError):
    pass


def normalize_whatsapp_number(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0"):
        digits = digits[1:]
    if not digits.startswith("55") and len(digits) in (10, 11):
        digits = f"55{digits}"
    if len(digits) < 12 or len(digits) > 15:
        raise WhatsAppError(
            "Número WhatsApp inválido. Use DDI+DDD+número, ex: 5511999999999."
        )
    return digits


def _provider() -> str:
    explicit = (getattr(settings, "whatsapp_provider", None) or "generic").lower()
    return explicit if explicit in ("generic", "evolution", "zapi") else "generic"


def _extract_message_id(data: dict[str, Any] | None) -> str | None:
    if not data:
        return None
    for key in ("messageId", "message_id", "id", "zaapId", "zaap_id"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    key_obj = data.get("key")
    if isinstance(key_obj, dict):
        nested = key_obj.get("id")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
    return None


def send_whatsapp_message(destinatario: str, mensagem: str) -> dict[str, Any]:
    if not settings.whatsapp_api_url:
        raise WhatsAppError(
            "WhatsApp não configurado. Defina WHATSAPP_API_URL e WHATSAPP_API_TOKEN no backend."
        )

    provider = _provider()
    number = normalize_whatsapp_number(destinatario)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = settings.whatsapp_api_token

    if token:
        if provider == "zapi":
            headers["Client-Token"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"

    if provider == "evolution":
        if token:
            headers["apikey"] = token
        payload = {"number": number, "text": mensagem}
    elif provider == "zapi":
        payload = {"phone": number, "message": mensagem}
    else:
        payload = {"number": number, "message": mensagem}

    response = httpx.post(
        settings.whatsapp_api_url,
        json=payload,
        headers=headers,
        timeout=30,
    )

    data: dict[str, Any] | None = None
    try:
        parsed = response.json()
        if isinstance(parsed, dict):
            data = parsed
    except Exception:
        data = None

    if response.status_code >= 400:
        detail = (data or {}).get("message") or response.text[:200]
        raise WhatsAppError(f"WhatsApp API erro {response.status_code}: {detail}")

    return {
        "provider": provider,
        "message_id": _extract_message_id(data),
        "normalized_number": number,
    }
