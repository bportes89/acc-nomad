"""Extrator do Demonstrativo Mensal Bradesco (colunas Crédito / Débito / Saldo)."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

import pymupdf as fitz

from acc_nomad.models import Transaction, TransactionNature

# Posições X das colunas (pdf.get_text dict), página de movimentação.
DOCTO_X = 215.0
CREDIT_X = 293.0
DEBIT_X = 395.0
SALDO_X = 498.0

DATE_LINE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{2,4})$")
AMOUNT_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")
DOCTO_RE = re.compile(r"^\d{3,8}$")
HEADER_LABELS = frozenset(
    {"DATA", "HISTORICO", "HISTÓRICO", "DOCTO", "CRÉDITO", "CREDITO", "DÉBITO", "DEBITO", "SALDO"}
)
SKIP_IN_DESC = ("SALDO ANTERIOR", "TOTAL DA MOVIMENTA", "LIMITE ESPECIAL")


def is_bradesco_mensal(text: str) -> bool:
    upper = text.upper()
    return "DEMONSTRATIVO MENSAL" in upper and "CONTA CORRENTE" in upper


def extract_bradesco_mensal(
    pdf_bytes: bytes,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Extrai lançamentos usando coordenadas das colunas Crédito/Débito."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    transactions: list[Transaction] = []
    seen: set[str] = set()
    current_date = date.today()

    try:
        for page_index, page in enumerate(doc):
            spans: list[tuple[float, float, float, float, str]] = []
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        bbox = span["bbox"]
                        spans.append((bbox[0], bbox[1], bbox[2], bbox[3], text))

            for row_y, items in _cluster_lines(spans):
                credit_raw: str | None = None
                debit_raw: str | None = None
                desc_parts: list[str] = []

                for x0, text in items:
                    date_match = DATE_LINE_RE.match(text)
                    if date_match:
                        parsed = _parse_date(*date_match.groups())
                        if parsed:
                            current_date = parsed
                        continue

                    upper = text.upper()
                    if upper in HEADER_LABELS:
                        continue

                    if x0 >= SALDO_X and AMOUNT_RE.match(text):
                        continue
                    if DEBIT_X <= x0 < SALDO_X and AMOUNT_RE.match(text):
                        debit_raw = text
                    elif CREDIT_X <= x0 < DEBIT_X and AMOUNT_RE.match(text):
                        credit_raw = text
                    elif DOCTO_X <= x0 < CREDIT_X and DOCTO_RE.match(text):
                        continue
                    elif x0 < DOCTO_X:
                        desc_parts.append(text)

                if not credit_raw and not debit_raw:
                    continue

                description = " ".join(desc_parts).strip()
                if not description or _should_skip(description):
                    continue

                tx_date = _date_from_description(description) or current_date
                is_credit = credit_raw is not None
                raw_amount = credit_raw or debit_raw
                assert raw_amount is not None

                tx = _build_transaction(
                    tx_date,
                    description,
                    raw_amount,
                    "C" if is_credit else "D",
                    default_category,
                )
                if tx and _remember(tx, page_index, row_y, seen):
                    transactions.append(tx)
    finally:
        doc.close()

    return transactions


def _cluster_lines(
    spans: list[tuple[float, float, float, float, str]],
    *,
    tolerance: float = 3.0,
) -> list[tuple[float, list[tuple[float, str]]]]:
    grouped: dict[float, list[tuple[float, str]]] = defaultdict(list)
    for x0, y0, _x1, _y1, text in spans:
        key = round(y0 / tolerance) * tolerance
        grouped[key].append((x0, text))

    return [(y, sorted(items, key=lambda item: item[0])) for y, items in sorted(grouped.items())]


def _parse_date(day: str, month: str, year: str) -> date | None:
    try:
        y = int(year)
        if y < 100:
            y += 2000 if y < 70 else 1900
        return date(y, int(month), int(day))
    except ValueError:
        return None


def _date_from_description(description: str) -> date | None:
    match = re.search(r"\b(\d{2})/(\d{2})(?:/(\d{2,4}))?\b", description)
    if not match:
        return None
    year = match.group(3)
    if not year:
        return None
    return _parse_date(match.group(1), match.group(2), year)


def _should_skip(description: str) -> bool:
    upper = description.upper()
    return any(keyword in upper for keyword in SKIP_IN_DESC)


def _build_transaction(
    tx_date: date,
    description: str,
    raw_amount: str,
    nature_flag: str,
    default_category: str | None,
) -> Transaction | None:
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


def _remember(tx: Transaction, page_index: int, row_y: float, seen: set[str]) -> bool:
    key = (
        f"{page_index}|{row_y}|{tx.date.isoformat()}|{tx.amount}|{tx.nature.value}"
    )
    if key in seen:
        return False
    seen.add(key)
    return True
