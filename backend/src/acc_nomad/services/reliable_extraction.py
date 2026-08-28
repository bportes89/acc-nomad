"""Extração confiável de lançamentos — escolhe a melhor estratégia e valida saldo."""

from __future__ import annotations

from dataclasses import dataclass

from acc_nomad.models import BankCode, Transaction
from acc_nomad.services.bank_rules import BankRules, get_bank_rules
from acc_nomad.services.bradesco_mensal_extractor import is_bradesco_mensal
from acc_nomad.services.columnar_pdf_extractor import (
    DEFAULT_BRADESCO_LAYOUT,
    detect_column_layout,
    extract_columnar_pdf,
    has_columnar_layout,
)
from acc_nomad.services.fallback_extractor import extract_all_local
from acc_nomad.services.saldo_validator import SaldoValidationResult, validate_saldo
from acc_nomad.services.transaction_utils import dedupe_transactions, prepare_transactions


@dataclass
class ExtractionOutcome:
    transactions: list[Transaction]
    saldo: SaldoValidationResult
    strategy: str


def extract_transactions_local(
    *,
    pdf_bytes: bytes,
    full_text: str,
    bank: BankCode,
    default_category: str | None = None,
) -> ExtractionOutcome:
    """Extrai lançamentos sem LLM — escolhe estratégia que fecha o saldo."""
    rules = get_bank_rules(bank)
    candidates: list[tuple[str, list[Transaction]]] = []

    if is_bradesco_mensal(full_text):
        layout = detect_column_layout(pdf_bytes) or DEFAULT_BRADESCO_LAYOUT
        columnar = extract_columnar_pdf(
            pdf_bytes, layout, default_category=default_category
        )
        if columnar:
            candidates.append(("bradesco_mensal", columnar))

    elif has_columnar_layout(pdf_bytes):
        layout = detect_column_layout(pdf_bytes)
        if layout:
            columnar = extract_columnar_pdf(
                pdf_bytes, layout, default_category=default_category
            )
            if columnar:
                candidates.append(("columnar", columnar))

    local = extract_all_local(full_text, default_category=default_category)
    if local:
        candidates.append(("regex_local", local))

    if not candidates:
        empty = validate_saldo(full_text, [], rules)
        return ExtractionOutcome([], empty, "none")

    best: ExtractionOutcome | None = None

    for strategy, raw_txs in candidates:
        prepared = prepare_transactions(raw_txs, full_text, rules)
        saldo = validate_saldo(full_text, prepared, rules)
        outcome = ExtractionOutcome(prepared, saldo, strategy)

        if saldo.ok and saldo.saldo_final is not None:
            return outcome

        if best is None:
            best = outcome
            continue

        best_delta = abs(best.saldo.delta or 999_999_999)
        new_delta = abs(saldo.delta or 999_999_999)
        if new_delta < best_delta:
            best = outcome
        elif new_delta == best_delta and len(prepared) > len(best.transactions):
            best = outcome

    assert best is not None
    return best


def extraction_saldo_ok(outcome: ExtractionOutcome) -> bool:
    saldo = outcome.saldo
    if saldo.saldo_final is None:
        return True
    return saldo.ok
