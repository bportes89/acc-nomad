"""Provedores de LLM para extração/classificação."""

from __future__ import annotations

import json
import logging
from typing import Literal

import httpx
from openai import OpenAI

from acc_nomad.config import settings

logger = logging.getLogger(__name__)

Provider = Literal["auto", "fallback", "gemini", "groq", "openai", "anthropic"]

_PROVIDER_ENV_KEYS: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


class LlmConfigError(RuntimeError):
    pass


class LlmCallError(RuntimeError):
    pass


def generate_json(system: str, user: str) -> dict:
    provider = _resolve_provider()
    if provider == "fallback":
        return {"transactions": []}

    explicit = settings.llm_provider.lower() != "auto"

    try:
        text = _call_provider(provider, system, user)
        return _parse_json_payload(text)
    except Exception as exc:
        logger.warning("LLM %s falhou: %s", provider, exc)
        if explicit:
            raise LlmCallError(f"Erro na API {provider}: {exc}") from exc
        return {"transactions": []}


def active_provider_name() -> str:
    try:
        return _resolve_provider()
    except LlmConfigError:
        return "fallback"


def _resolve_provider() -> str:
    explicit = settings.llm_provider.lower()
    if explicit != "auto":
        if explicit == "fallback":
            return "fallback"
        _require_api_key(explicit)
        return explicit

    if settings.anthropic_api_key:
        return "anthropic"
    if settings.gemini_api_key:
        return "gemini"
    if settings.groq_api_key:
        return "groq"
    if settings.openai_api_key:
        return "openai"
    return "fallback"


def _require_api_key(provider: str) -> None:
    env_key = _PROVIDER_ENV_KEYS.get(provider)
    if not env_key:
        return
    key_map = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "GROQ_API_KEY": settings.groq_api_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
    }
    if not key_map.get(env_key):
        raise LlmConfigError(
            f"LLM_PROVIDER={provider} mas {env_key} não está definida no backend/.env (ou Render)."
        )


def _call_provider(provider: str, system: str, user: str) -> str:
    if provider == "gemini":
        return _call_gemini(system, user)
    if provider == "groq":
        return _call_openai_compatible(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            system=system,
            user=user,
        )
    if provider == "openai":
        return _call_openai_compatible(
            base_url=None,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            system=system,
            user=user,
        )
    if provider == "anthropic":
        return _call_anthropic(system, user)
    return "{}"


def _call_gemini(system: str, user: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }
    response = httpx.post(
        url,
        params={"key": settings.gemini_api_key},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    parts = data["candidates"][0]["content"]["parts"]
    return parts[0]["text"]


def _call_openai_compatible(
    *,
    base_url: str | None,
    api_key: str,
    model: str,
    system: str,
    user: str,
) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or "{}"


def _call_anthropic(system: str, user: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _parse_json_payload(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise LlmCallError("Resposta da LLM não contém JSON válido.")
    return json.loads(text[start : end + 1])
