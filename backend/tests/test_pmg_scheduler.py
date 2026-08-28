"""Testes do agendamento PMG semanal."""

from datetime import date

from acc_nomad.services.pmg_calculator import calcular_pmg_resumo
from acc_nomad.services.pmg_scheduler import previous_month_period


def test_previous_month_period_january():
    periodo, inicio, fim = previous_month_period(date(2026, 1, 15))
    assert periodo == "2025-12"
    assert inicio == date(2025, 12, 1)
    assert fim == date(2025, 12, 31)


def test_previous_month_period_march():
    periodo, inicio, fim = previous_month_period(date(2026, 3, 10))
    assert periodo == "2026-02"
    assert inicio == date(2026, 2, 1)
    assert fim == date(2026, 2, 28)


def test_calcular_pmg_resumo_receita():
    lancamentos = [
        {"valor": 1000, "natureza": "credito", "categoria": "receita"},
        {"valor": 200, "natureza": "debito", "categoria": "fornecedor"},
    ]
    resumo = calcular_pmg_resumo(lancamentos, [])
    assert resumo["receita"] == 1000
    assert resumo["custo_variavel"] == 200
