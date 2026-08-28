"""Organização cronológica — substitui nó Code do n8n."""

from __future__ import annotations

from acc_nomad.models import BankCode, Transaction
from acc_nomad.services.bank_rules import get_bank_rules


def sort_transactions(transactions: list[Transaction], bank: BankCode) -> list[Transaction]:
    rules = get_bank_rules(bank)
    return sorted(transactions, key=lambda tx: tx.date, reverse=rules.sort_reverse)
