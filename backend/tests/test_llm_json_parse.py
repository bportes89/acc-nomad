"""Testes de parsing JSON da LLM."""

from acc_nomad.services.llm_providers import _parse_json_payload, _salvage_transactions_json


def test_salvage_truncated_transactions():
    raw = """{
  "transactions": [
    {"date": "2026-01-02", "description": "Pix", "amount": 100.0, "nature": "credito", "category": "Receita"},
    {"date": "2026-01-03", "description": "Aluguel", "amount": 50.0, "nature": "debito", "category": "Aluguel"},
    {"date": "2026-01-04", "description": "Incompleto"
"""
    result = _salvage_transactions_json(raw)
    assert result is not None
    assert len(result["transactions"]) == 2


def test_parse_json_payload_salvages_on_truncation():
    text = '{"transactions": [{"date": "2026-01-01", "description": "A", "amount": 1, "nature": "debito", "category": "X"}'
    parsed = _parse_json_payload(text)
    assert len(parsed["transactions"]) == 1
