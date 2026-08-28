"""Detecção de banco — substitui Switch Node + OpenAI do n8n."""

from __future__ import annotations

from openai import OpenAI

from acc_nomad.config import settings
from acc_nomad.models import BankCode

BANK_DETECTION_PROMPT = """Analise o texto extraído de um extrato bancário brasileiro.
Identifique o banco emissor com base em marcas, cabeçalhos e padrões estruturais.

Responda APENAS com um destes códigos (minúsculo):
bb, bradesco, santander, sicredi, sicoob, basa, itau, unicredi, unknown
"""

BANK_ALIASES: dict[str, BankCode] = {
    "banco do brasil": BankCode.BB,
    "ouvidoria bb": BankCode.BB,
    "bb giro": BankCode.BB,
    "bradesco": BankCode.BRADESCO,
    "santander": BankCode.SANTANDER,
    "sicredi": BankCode.SICREDI,
    "sicoob": BankCode.SICOOB,
    "basa": BankCode.BASA,
    "itau": BankCode.ITAU,
    "itaú": BankCode.ITAU,
    "unicredi": BankCode.UNICREDI,
}


def detect_bank_from_text(sample_text: str) -> BankCode:
    lowered = sample_text.lower()
    for alias, code in BANK_ALIASES.items():
        if alias in lowered:
            return code

    if not settings.openai_api_key:
        return BankCode.UNKNOWN

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": BANK_DETECTION_PROMPT},
            {"role": "user", "content": sample_text[:6000]},
        ],
    )
    raw = (response.choices[0].message.content or "unknown").strip().lower()
    try:
        return BankCode(raw)
    except ValueError:
        return BankCode.UNKNOWN
