#!/usr/bin/env python3
"""Gera PDF de teste estilo Bradesco (substituto quando Drive bloqueia)."""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pymupdf as fitz

DESCRICOES_CREDITO = [
    "PIX RECEBIDO REM: CLIENTE {n}",
    "TED-CREDITO EM CONTA REM: EMPRESA {n}",
    "DEP CHQ NUM {n}",
    "TRANSFERENCIA PIX REM: {n}",
]
DESCRICOES_DEBITO = [
    "TARIFA PACOTE SERVICOS",
    "PIX ENVIADO PARA FORNECEDOR {n}",
    "PAGAMENTO BOLETO {n}",
    "TED ENVIADA FORNECEDOR {n} LTDA",
    "DEBITO AUTOMATICO ENERGIA",
]


def _br(value: float) -> str:
    whole = int(value)
    cents = int(round((value - whole) * 100))
    return f"{whole:,}".replace(",", ".") + f",{cents:02d}"


def generate_bradesco_pdf(
    output: Path,
    *,
    pages: int = 29,
    txs_per_page: int = 8,
    saldo_inicial: float = 50_000.0,
) -> Path:
    doc = fitz.open()
    start = date(2025, 1, 2)
    saldo = saldo_inicial
    tx_index = 0

    for page_num in range(pages):
        page = doc.new_page(width=595, height=842)
        y = 40
        if page_num == 0:
            page.insert_text((40, y), "Bradesco - Extrato de Conta Corrente", fontsize=11)
            y += 20
            page.insert_text((40, y), f"SALDO ANTERIOR {_br(saldo_inicial)} C", fontsize=9)
            y += 24
        else:
            page.insert_text((40, y), f"Bradesco - Extrato (continuação pág. {page_num + 1})", fontsize=9)
            y += 24

        for _ in range(txs_per_page):
            tx_index += 1
            tx_date = start + timedelta(days=tx_index % 28)
            is_credit = random.random() < 0.45
            amount = round(random.uniform(15, 3500), 2)
            if is_credit:
                saldo += amount
                desc = random.choice(DESCRICOES_CREDITO).format(n=tx_index)
                flag = "C"
            else:
                saldo -= amount
                desc = random.choice(DESCRICOES_DEBITO).format(n=tx_index)
                flag = "D"

            page.insert_text((40, y), tx_date.strftime("%d/%m/%Y"), fontsize=8)
            y += 12
            page.insert_text((40, y), desc[:70], fontsize=8)
            y += 12
            page.insert_text((40, y), f"{_br(amount)} {flag}", fontsize=8)
            y += 16
            if y > 780:
                break

        if page_num == pages - 1:
            page.insert_text((40, y + 8), f"SALDO FINAL {_br(round(saldo, 2))} C", fontsize=9)

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    doc.close()
    return output


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        __file__).resolve().parents[2] / "docs" / "EXTRATOS EXEMPLO" / "bradesco-sintetico-29p.pdf"
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 29
    path = generate_bradesco_pdf(out, pages=pages)
    print(f"Gerado: {path} ({pages} páginas)")


if __name__ == "__main__":
    main()
