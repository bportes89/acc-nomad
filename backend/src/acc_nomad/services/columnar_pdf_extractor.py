"""Extrator genérico para PDFs tabulares (colunas Crédito / Débito / Saldo)."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

import pymupdf as fitz

from acc_nomad.models import Transaction, TransactionNature

DATE_LINE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{2,4})$")
AMOUNT_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")
DOCTO_RE = re.compile(r"^\d{3,8}$")
HEADER_LABELS = frozenset(
    {"DATA", "HISTORICO", "HISTÓRICO", "DOCTO", "CRÉDITO", "CREDITO", "DÉBITO", "DEBITO", "SALDO"}
)
SKIP_IN_DESC = ("SALDO ANTERIOR", "TOTAL DA MOVIMENTA", "LIMITE ESPECIAL")


@dataclass(frozen=True)
class ColumnLayout:
    docto_x: float
    credit_x: float
    debit_x: float
    saldo_x: float


# Layout calibrado no Demonstrativo Mensal Bradesco (fallback se detecção falhar).
DEFAULT_BRADESCO_LAYOUT = ColumnLayout(
    docto_x=215.0,
    credit_x=293.0,
    debit_x=395.0,
    saldo_x=498.0,
)


def detect_column_layout(pdf_bytes: bytes, *, max_pages: int = 8) -> ColumnLayout | None:
    """Detecta colunas Crédito/Débito/Saldo a partir da linha de cabeçalho."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        credit_x = debit_x = saldo_x = docto_x = None

        for page in doc[:max_pages]:
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    row: list[tuple[float, str]] = []
                    for span in spans:
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        row.append((span["bbox"][0], text.upper()))

                    if len(row) < 3:
                        continue

                    for x0, label in row:
                        kind = _header_kind(label)
                        if kind == "credit":
                            credit_x = x0
                        elif kind == "debit":
                            debit_x = x0
                        elif kind == "saldo":
                            saldo_x = x0
                        elif kind == "docto":
                            docto_x = x0

                    if credit_x is not None and debit_x is not None and saldo_x is not None:
                        return ColumnLayout(
                            docto_x=docto_x or (credit_x - 70),
                            credit_x=credit_x,
                            debit_x=debit_x,
                            saldo_x=saldo_x,
                        )
        return None
    finally:
        doc.close()


def has_columnar_layout(pdf_bytes: bytes) -> bool:
    return detect_column_layout(pdf_bytes) is not None


def _header_kind(label: str) -> str | None:
    normalized = (
        label.upper()
        .replace("Ó", "O")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ú", "U")
    )
    if "CRED" in normalized:
        return "credit"
    if "DEB" in normalized:
        return "debit"
    if normalized == "SALDO":
        return "saldo"
    if normalized == "DOCTO":
        return "docto"
    return None


def extract_columnar_pdf(
    pdf_bytes: bytes,
    layout: ColumnLayout,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Extrai lançamentos pelas colunas Crédito/Débito do PDF."""
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

                    if x0 >= layout.saldo_x and AMOUNT_RE.match(text):
                        continue
                    if layout.debit_x <= x0 < layout.saldo_x and AMOUNT_RE.match(text):
                        debit_raw = text
                    elif layout.credit_x <= x0 < layout.debit_x and AMOUNT_RE.match(text):
                        credit_raw = text
                    elif layout.docto_x <= x0 < layout.credit_x and DOCTO_RE.match(text):
                        continue
                    elif x0 < layout.docto_x:
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
    if not match or not match.group(3):
        return None
    return _parse_date(match.group(1), match.group(2), match.group(3))


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
    category = (
        default_category
        if nature == TransactionNature.CREDIT and default_category
        else "Não classificado (fallback)"
    )

    return Transaction(
        date=tx_date,
        description=description[:200],
        amount=amount,
        nature=nature,
        category=category,
    )


def _remember(tx: Transaction, page_index: int, row_y: float, seen: set[str]) -> bool:
    key = f"{page_index}|{row_y}|{tx.date.isoformat()}|{tx.amount}|{tx.nature.value}"
    if key in seen:
        return False
    seen.add(key)
    return True
