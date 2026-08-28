"""Testes de validação de saldo."""

from datetime import date

from acc_nomad.models import BankCode, Transaction, TransactionNature
from acc_nomad.services.bank_rules import get_bank_rules
from acc_nomad.services.saldo_validator import parse_br_amount, validate_saldo


def _tx(amount: float, nature: TransactionNature, day: int = 10) -> Transaction:
    return Transaction(
        date=date(2025, 1, day),
        description="Teste",
        amount=amount,
        nature=nature,
    )


def test_parse_br_amount():
    assert parse_br_amount("1.234,56") == 1234.56


def test_saldo_ok():
    text = """
    SALDO ANTERIOR 1.000,00
    10/01/2025 PIX RECEBIDO 500,00 C
    11/01/2025 PAGAMENTO 200,00 D
    SALDO FINAL 1.300,00
    """
    txs = [_tx(500, TransactionNature.CREDIT, 10), _tx(200, TransactionNature.DEBIT, 11)]
    result = validate_saldo(text, txs, get_bank_rules(BankCode.SICOOB))
    assert result.ok is True
    assert result.saldo_inicial == 1000.0
    assert result.saldo_final == 1300.0
    assert result.saldo_calculado == 1300.0


def test_saldo_divergente():
    text = "SALDO ANTERIOR 100,00\nSALDO FINAL 500,00"
    txs = [_tx(50, TransactionNature.CREDIT)]
    result = validate_saldo(text, txs, get_bank_rules(BankCode.BB))
    assert result.ok is False
    assert result.delta == 150.0 - 500.0


def test_itau_sort_reverse():
    rules = get_bank_rules(BankCode.ITAU)
    assert rules.sort_reverse is True


def test_bb_sort_ascending():
    rules = get_bank_rules(BankCode.BRADESCO)
    assert rules.sort_reverse is False
