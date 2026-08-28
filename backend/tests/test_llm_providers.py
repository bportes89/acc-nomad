"""Testes de resolução do provedor LLM."""

import pytest

from acc_nomad.config import settings
from acc_nomad.services.llm_providers import LlmConfigError, _resolve_provider


def test_explicit_anthropic_without_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    with pytest.raises(LlmConfigError, match="ANTHROPIC_API_KEY"):
        _resolve_provider()


def test_explicit_anthropic_with_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")
    assert _resolve_provider() == "anthropic"


def test_auto_prefers_anthropic_when_multiple_keys(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "auto")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key")
    assert _resolve_provider() == "anthropic"
