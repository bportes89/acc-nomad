"""Validação de saldos — saldo anterior + movimentações vs saldo final."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from acc_nomad.models import Transaction, TransactionNature
from acc_nomad.services.bank_rules import BankRules

AMOUNT_BR_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})")
TOLERANCE = 0.02


@dataclass
class SaldoValidationResult:
    ok: bool
    saldo_inicial: float | None = None
    saldo_final: float | None = None
    saldo_calculado: float | None = None
    delta: float | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "saldo_inicial": self.saldo_inicial,
            "saldo_final": self.saldo_final,
            "saldo_calculado": self.saldo_calculado,
            "delta": self.delta,
            "warnings": self.warnings,
        }


def parse_br_amount(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "."))


def validate_saldo(
    full_text: str,
    transactions: list[Transaction],
    rules: BankRules,
) -> SaldoValidationResult:
    warnings: list[str] = []
    saldo_inicial = _extract_saldo_by_keywords(full_text, rules.saldo_anterior_keywords)
    saldo_final = _extract_saldo_final(full_text, rules.saldo_final_keywords)

    if not transactions:
        return SaldoValidationResult(
            ok=False,
            saldo_inicial=saldo_inicial,
            saldo_final=saldo_final,
            warnings=["Nenhum lançamento para validar saldo."],
        )

    base = saldo_inicial if saldo_inicial is not None else 0.0
    if saldo_inicial is None:
        warnings.append("Saldo anterior não encontrado no PDF — cálculo assume R$ 0,00.")

    saldo_corrente = base
    total_credito = 0.0
    total_debito = 0.0

    for tx in transactions:
        if tx.nature == TransactionNature.CREDIT:
            saldo_corrente += tx.amount
            total_credito += tx.amount
        else:
            saldo_corrente -= tx.amount
            total_debito += tx.amount

    saldo_calculado = round(saldo_corrente, 2)

    if saldo_final is None:
        warnings.append("Saldo final não encontrado no PDF — validação parcial.")
        return SaldoValidationResult(
            ok=True,
            saldo_inicial=saldo_inicial,
            saldo_final=None,
            saldo_calculado=saldo_calculado,
            delta=None,
            warnings=warnings,
        )

    delta = round(saldo_calculado - saldo_final, 2)
    ok = abs(delta) <= TOLERANCE

    if not ok:
        warnings.append(
            f"Divergência de saldo: calculado R$ {saldo_calculado:,.2f} "
            f"vs extrato R$ {saldo_final:,.2f} (Δ R$ {delta:,.2f})."
        )

    if total_credito == 0 and total_debito == 0:
        warnings.append("Nenhum movimento com valor detectado.")

    return SaldoValidationResult(
        ok=ok,
        saldo_inicial=saldo_inicial,
        saldo_final=saldo_final,
        saldo_calculado=saldo_calculado,
        delta=delta,
        warnings=warnings,
    )


def _extract_saldo_by_keywords(text: str, keywords: tuple[str, ...]) -> float | None:
    upper = text.upper()
    for keyword in keywords:
        pattern = re.compile(
            rf"{re.escape(keyword)}[^\d]{{0,40}}{AMOUNT_BR_RE.pattern}",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(upper)
        if match:
            return parse_br_amount(match.group(1))
    return None


def _extract_saldo_final(text: str, keywords: tuple[str, ...]) -> float | None:
    upper = text.upper()
    last_amount: float | None = None

    for keyword in keywords:
        pattern = re.compile(
            rf"{re.escape(keyword)}[^\d]{{0,40}}{AMOUNT_BR_RE.pattern}",
            re.IGNORECASE,
        )
        for match in pattern.finditer(upper):
            last_amount = parse_br_amount(match.group(1))

    if last_amount is not None:
        return last_amount

    trailing = list(AMOUNT_BR_RE.finditer(text))
    if len(trailing) >= 2:
        return parse_br_amount(trailing[-1].group(1))

    return None
