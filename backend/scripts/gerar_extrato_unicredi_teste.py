#!/usr/bin/env python3
"""Gera PDF de teste estilo Unicredi (cooperativa — linha única com C/D)."""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pymupdf as fitz


def _br(value: float) -> str:
    whole = int(value)
    cents = int(round((value - whole) * 100))
    return f"{whole:,}".replace(",", ".") + f",{cents:02d}"


def generate_unicredi_pdf(output: Path, *, pages: int = 5, txs_per_page: int = 10) -> Path:
    doc = fitz.open()
    start = date(2026, 7, 1)
    saldo = 25_000.0
    tx_index = 0

    for page_num in range(pages):
        page = doc.new_page(width=595, height=842)
        y = 40
        page.insert_text((40, y), "UNICREDI DO BRASIL - Extrato Conta Corrente", fontsize=11)
        y += 18
        page.insert_text((40, y), "Cooperativa 1234 - Período: 01/07/2026 a 31/07/2026", fontsize=8)
        y += 22
        if page_num == 0:
            page.insert_text((40, y), f"SDO ANT {_br(saldo)} C", fontsize=8)
            y += 18
        page.insert_text(
            (40, y), "Dt.Movimento  Histórico  Documento  Valor(R$)  Saldo(R$)", fontsize=7
        )
        y += 16

        for _ in range(txs_per_page):
            tx_index += 1
            tx_date = start + timedelta(days=tx_index % 30)
            is_credit = random.random() < 0.4
            amount = round(random.uniform(20, 2800), 2)
            if is_credit:
                saldo += amount
                desc = f"PIX RECEBIDO REM {tx_index}"
                flag = "C"
            else:
                saldo -= amount
                desc = f"TARIFA / PAGAMENTO {tx_index}"
                flag = "D"

            line = (
                f"{tx_date.strftime('%d/%m/%Y')}  {desc}  {tx_index:06d}  "
                f"{_br(amount)} {flag}  {_br(round(saldo, 2))} {flag}"
            )
            page.insert_text((40, y), line[:95], fontsize=7)
            y += 12
            if y > 780:
                break

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    doc.close()
    return output


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        __file__).resolve().parents[2] / "docs" / "EXTRATOS EXEMPLO" / "unicredi-sintetico-jul26.pdf"
    path = generate_unicredi_pdf(out)
    print(f"Gerado: {path}")


if __name__ == "__main__":
    main()
