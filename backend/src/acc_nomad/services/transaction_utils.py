"""Utilitários de pós-processamento de lançamentos."""

from __future__ import annotations

from acc_nomad.models import Transaction
from acc_nomad.services.bank_rules import BankRules
from acc_nomad.services.saldo_validator import validate_saldo


def dedupe_transactions(transactions: list[Transaction]) -> list[Transaction]:
    seen: set[str] = set()
    result: list[Transaction] = []

    for tx in transactions:
        key = (
            f"{tx.date.isoformat()}|{tx.description.strip()[:80]}|"
            f"{tx.amount:.2f}|{tx.nature.value}"
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(tx)

    return result


def prepare_transactions(
    transactions: list[Transaction],
    full_text: str,
    rules: BankRules,
) -> list[Transaction]:
    """Deduplica só se o saldo continuar batendo com o PDF."""
    if not transactions:
        return transactions

    saldo_raw = validate_saldo(full_text, transactions, rules)
    if saldo_raw.ok or saldo_raw.saldo_final is None:
        return transactions

    deduped = dedupe_transactions(transactions)
    if len(deduped) == len(transactions):
        return transactions

    saldo_deduped = validate_saldo(full_text, deduped, rules)
    if saldo_deduped.ok:
        return deduped

    raw_delta = abs(saldo_raw.delta or 0)
    deduped_delta = abs(saldo_deduped.delta or 0)
    if deduped_delta < raw_delta:
        return deduped
    return transactions
