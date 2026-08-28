"""Extrator do Demonstrativo Mensal Bradesco (colunas Crédito / Débito / Saldo)."""

from __future__ import annotations

from acc_nomad.models import Transaction
from acc_nomad.services.columnar_pdf_extractor import (
    DEFAULT_BRADESCO_LAYOUT,
    detect_column_layout,
    extract_columnar_pdf,
)


def is_bradesco_mensal(text: str) -> bool:
    upper = text.upper()
    return "DEMONSTRATIVO MENSAL" in upper and "CONTA CORRENTE" in upper


def extract_bradesco_mensal(
    pdf_bytes: bytes,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    layout = detect_column_layout(pdf_bytes) or DEFAULT_BRADESCO_LAYOUT
    return extract_columnar_pdf(pdf_bytes, layout, default_category=default_category)
