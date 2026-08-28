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


def generate_json(
    system: str,
    user: str,
    *,
    fast: bool = False,
    max_tokens: int | None = None,
) -> dict:
    provider = _resolve_provider()
    if provider == "fallback":
        return {"transactions": []}

    explicit = settings.llm_provider.lower() != "auto"

    try:
        text = _call_provider(provider, system, user, fast=fast, max_tokens=max_tokens)
        return _parse_json_payload(text)
    except json.JSONDecodeError as exc:
        logger.warning("LLM %s retornou JSON inválido: %s", provider, exc)
        return {"transactions": []}
    except Exception as exc:
        logger.warning("LLM %s falhou: %s", provider, exc)
        if explicit:
            hint = ""
            if provider == "anthropic" and "not_found_error" in str(exc):
                model = settings.anthropic_model_fast if fast else settings.anthropic_model
                hint = f" Verifique ANTHROPIC_MODEL (atual: {model})."
            raise LlmCallError(f"Erro na API {provider}: {exc}{hint}") from exc
        return {"transactions": []}


def generate_json_fast(system: str, user: str) -> dict:
    """Classificação rápida — usa Haiku quando Anthropic está configurado."""
    return generate_json(system, user, fast=True, max_tokens=4096)


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


def _call_provider(
    provider: str,
    system: str,
    user: str,
    *,
    fast: bool = False,
    max_tokens: int | None = None,
) -> str:
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
        return _call_anthropic(system, user, fast=fast, max_tokens=max_tokens)
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


def _call_anthropic(
    system: str,
    user: str,
    *,
    fast: bool = False,
    max_tokens: int | None = None,
) -> str:
    from anthropic import Anthropic

    model = settings.anthropic_model_fast if fast else settings.anthropic_model
    tokens = max_tokens if max_tokens is not None else (4096 if fast else 8192)
    client = Anthropic(api_key=settings.anthropic_api_key, timeout=90.0 if fast else 120.0)
    response = client.messages.create(
        model=model,
        max_tokens=tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _parse_json_payload(text: str) -> dict:
    start = text.find("{")
    if start == -1:
        raise LlmCallError("Resposta da LLM não contém JSON válido.")
    end = text.rfind("}")
    raw = text[start : end + 1] if end > start else text[start:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        salvaged = _salvage_transactions_json(raw)
        if salvaged:
            logger.info("JSON parcial recuperado: %d lançamentos", len(salvaged["transactions"]))
            return salvaged
        raise


def _salvage_transactions_json(raw: str) -> dict | None:
    """Extrai objetos completos de transactions[] quando o JSON veio truncado."""
    key = '"transactions"'
    idx = raw.find(key)
    if idx == -1:
        return None
    arr_start = raw.find("[", idx)
    if arr_start == -1:
        return None

    items: list[dict] = []
    i = arr_start + 1
    length = len(raw)

    while i < length:
        while i < length and raw[i] in " \n\r\t,":
            i += 1
        if i >= length or raw[i] == "]":
            break
        if raw[i] != "{":
            break

        depth = 0
        obj_start = i
        in_string = False
        escape = False
        closed = False

        for j in range(i, length):
            ch = raw[j]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        items.append(json.loads(raw[obj_start : j + 1]))
                    except json.JSONDecodeError:
                        pass
                    i = j + 1
                    closed = True
                    break
        if not closed:
            break

    if not items:
        return None
    return {"transactions": items}
