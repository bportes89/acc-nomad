"""Extrator básico sem IA — para dev/testes quando Claude não está configurado."""

from __future__ import annotations

import re
from datetime import date

from acc_nomad.models import Transaction, TransactionNature

DATE_RE = re.compile(r"\b(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})\b")
AMOUNT_LINE_RE = re.compile(
    r"^(\d{1,3}(?:\.\d{3})*,\d{2})\s*([CD])\s*$",
    re.IGNORECASE,
)
INLINE_AMOUNT_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*([CD])\b",
    re.IGNORECASE,
)
SKIP_KEYWORDS = (
    "SALDO ANTERIOR",
    "S A L D O",
    "LIMITE ESPECIAL",
    "TAXA ",
    "CUSTO EFETIVO",
    "INFORMAC",
    "OBSERV",
    "SAC ",
    "OUVIDORIA",
)


def extract_fallback(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    transactions: list[Transaction] = []
    seen: set[str] = set()
    lines = [ln.strip() for ln in sample_text.splitlines() if ln.strip()]

    current_date: date | None = None
    description_parts: list[str] = []

    for line in lines:
        upper = line.upper()

        date_match = DATE_RE.search(line)
        if date_match and line.count("/") >= 2 and len(line) <= 20:
            day, month, year = date_match.groups()
            try:
                current_date = date(int(year), int(month), int(day))
            except ValueError:
                pass
            continue

        amount_line = AMOUNT_LINE_RE.match(line)
        if amount_line and current_date:
            raw_amount, nature_flag = amount_line.groups()
            desc = " ".join(description_parts).strip()
            if _should_skip(desc, upper):
                description_parts = []
                continue

            tx = _build_transaction(
                current_date, desc, raw_amount, nature_flag, default_category
            )
            if tx and _remember(tx, seen):
                transactions.append(tx)
            description_parts = []
            continue

        inline = INLINE_AMOUNT_RE.search(line)
        if inline and current_date:
            raw_amount, nature_flag = inline.groups()
            desc = DATE_RE.sub("", line)
            desc = INLINE_AMOUNT_RE.sub("", desc).strip(" -|")
            if desc and not _should_skip(desc, desc.upper()):
                tx = _build_transaction(
                    current_date, desc, raw_amount, nature_flag, default_category
                )
                if tx and _remember(tx, seen):
                    transactions.append(tx)
            continue

        if current_date and not _is_noise_line(line):
            description_parts.append(line)

    return transactions[:200]


def _build_transaction(
    tx_date: date,
    description: str,
    raw_amount: str,
    nature_flag: str,
    default_category: str | None = None,
) -> Transaction | None:
    if not description or len(description) < 3:
        return None

    amount = float(raw_amount.replace(".", "").replace(",", "."))
    if amount <= 0:
        return None

    nature = (
        TransactionNature.CREDIT
        if nature_flag.upper() == "C"
        else TransactionNature.DEBIT
    )

    if nature == TransactionNature.CREDIT and default_category:
        category = default_category
    else:
        category = "Não classificado (fallback)"

    return Transaction(
        date=tx_date,
        description=description[:200],
        amount=amount,
        nature=nature,
        category=category,
    )


def _should_skip(description: str, upper: str) -> bool:
    if not description:
        return True
    return any(k in upper for k in SKIP_KEYWORDS)


def _is_noise_line(line: str) -> bool:
    if DATE_RE.fullmatch(line.replace(" ", "")):
        return True
    if line.isdigit():
        return True
    if re.fullmatch(r"\d{3}-\d", line):
        return True
    return False


def _remember(tx: Transaction, seen: set[str]) -> bool:
    key = f"{tx.date.isoformat()}|{tx.description}|{tx.amount}|{tx.nature.value}"
    if key in seen:
        return False
    seen.add(key)
    return True
