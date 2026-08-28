from acc_nomad.models import Transaction, TransactionNature
from acc_nomad.services.bank_rules import get_bank_rules
from acc_nomad.services.transaction_utils import dedupe_transactions, prepare_transactions
from acc_nomad.models import BankCode
from datetime import date


def _tx(amount: float, nature: TransactionNature, desc: str = "PIX") -> Transaction:
    return Transaction(
        date=date(2026, 7, 1),
        description=desc,
        amount=amount,
        nature=nature,
        category="Receita de vendas",
    )


def test_prepare_transactions_keeps_duplicates_when_dedupe_breaks_saldo():
    text = "SALDO ANTERIOR\n100,00\nSALDO FINAL\n99,40"
    txs = [
        _tx(0.30, TransactionNature.DEBIT, "TARIFA BANCARIA"),
        _tx(0.30, TransactionNature.DEBIT, "TARIFA BANCARIA"),
    ]
    rules = get_bank_rules(BankCode.BRADESCO)

    prepared = prepare_transactions(txs, text, rules)
    assert len(prepared) == 2
    assert len(dedupe_transactions(txs)) == 1


def test_prepare_transactions_applies_dedupe_when_saldo_still_ok():
    text = "SALDO ANTERIOR\n100,00\nSALDO FINAL\n150,00"
    txs = [
        _tx(50, TransactionNature.CREDIT, "PIX A"),
        _tx(50, TransactionNature.CREDIT, "PIX A"),
    ]
    rules = get_bank_rules(BankCode.BB)

    prepared = prepare_transactions(txs, text, rules)
    assert len(prepared) == 1
