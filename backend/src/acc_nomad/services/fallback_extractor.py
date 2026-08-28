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
DATE_ONLY_RE = re.compile(r"^(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})$")
RS_AMOUNT_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
DEBIT_HINTS = ("PAGAMENTO", "DEBITO", "DÉBITO", "TARIFA", "TAXA", "SAQUE", "ENVIO PIX")
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

    return transactions[:500]


def extract_all_local(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Extrai lançamentos com regex (Bradesco C/D, Sicoob R$, etc.)."""
    seen: set[str] = set()
    merged: list[Transaction] = []
    for tx in extract_fallback(sample_text, default_category=default_category):
        if _remember(tx, seen):
            merged.append(tx)
    for tx in _extract_rs_table(sample_text, default_category=default_category):
        if _remember(tx, seen):
            merged.append(tx)
    return merged


def _extract_rs_table(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Extratos cooperativas / PIX com valores em R$."""
    lines = [ln.strip() for ln in sample_text.splitlines() if ln.strip()]
    transactions: list[Transaction] = []
    current_date: date | None = None

    for index, line in enumerate(lines):
        if DATE_ONLY_RE.match(line):
            match = DATE_ONLY_RE.match(line)
            assert match is not None
            day, month, year = match.groups()
            try:
                current_date = date(int(year), int(month), int(day))
            except ValueError:
                current_date = None
            continue

        amount_match = RS_AMOUNT_RE.search(line)
        if not amount_match or not current_date:
            continue

        raw_amount = amount_match.group(1)
        desc = _description_before_amount(lines, index)
        if not desc or _should_skip(desc, desc.upper()):
            continue

        nature_flag = "D" if any(h in desc.upper() for h in DEBIT_HINTS) else "C"
        tx = _build_transaction(current_date, desc, raw_amount, nature_flag, default_category)
        if tx:
            transactions.append(tx)

    return transactions


def _description_before_amount(lines: list[str], amount_index: int) -> str:
    parts: list[str] = []
    for j in range(amount_index - 1, max(amount_index - 10, -1), -1):
        line = lines[j]
        if DATE_ONLY_RE.match(line) or RS_AMOUNT_RE.search(line):
            break
        if _is_noise_line(line) or line in ("-", "Recebimento", "REAL"):
            continue
        if line.startswith("E") and len(line) > 20:
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}$", line):
            continue
        parts.insert(0, line)
        if len(parts) >= 3:
            break
    return " ".join(parts).strip()[:200]


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
