"""Utilitários de pós-processamento de lançamentos."""

from __future__ import annotations

from acc_nomad.models import Transaction


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
