"""Provedores de LLM para extração/classificação — inclui opções gratuitas."""

from __future__ import annotations

import json
from typing import Literal

import httpx
from openai import OpenAI

from acc_nomad.config import settings

Provider = Literal["auto", "fallback", "gemini", "groq", "openai", "anthropic"]


def generate_json(system: str, user: str) -> dict:
    provider = _resolve_provider()
    if provider == "fallback":
        return {"transactions": []}

    try:
        if provider == "gemini":
            text = _call_gemini(system, user)
        elif provider == "groq":
            text = _call_openai_compatible(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                system=system,
                user=user,
            )
        elif provider == "openai":
            text = _call_openai_compatible(
                base_url=None,
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                system=system,
                user=user,
            )
        elif provider == "anthropic":
            text = _call_anthropic(system, user)
        else:
            return {"transactions": []}
        return _parse_json_payload(text)
    except Exception:
        return {"transactions": []}


def active_provider_name() -> str:
    return _resolve_provider()


def _resolve_provider() -> str:
    explicit = settings.llm_provider.lower()
    if explicit != "auto":
        return explicit

    if settings.gemini_api_key:
        return "gemini"
    if settings.groq_api_key:
        return "groq"
    if settings.openai_api_key:
        return "openai"
    if settings.anthropic_api_key:
        return "anthropic"
    return "fallback"


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
        return {"transactions": []}
    return json.loads(text[start : end + 1])
