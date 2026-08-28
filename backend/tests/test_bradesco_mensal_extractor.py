from pathlib import Path

import pytest

from acc_nomad.models import BankCode
from acc_nomad.services.bradesco_mensal_extractor import (
    extract_bradesco_mensal,
    is_bradesco_mensal,
)
from acc_nomad.services.pdf_analyzer import extract_full_text
from acc_nomad.services.saldo_validator import validate_saldo
from acc_nomad.services.bank_rules import get_bank_rules

CLIENT_PDF = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "EXTRATOS EXEMPLO"
    / "EXTRATO_MENSAL_070826_163304 (2).pdf"
)


def test_is_bradesco_mensal():
    assert is_bradesco_mensal("Demonstrativo Mensal - Conta Corrente\nBradesco")
    assert not is_bradesco_mensal("Extrato de Conta Corrente\nBradesco")


@pytest.mark.skipif(not CLIENT_PDF.is_file(), reason="PDF de exemplo da cliente ausente")
def test_extract_bradesco_mensal_client_pdf():
    pdf_bytes = CLIENT_PDF.read_bytes()
    text = extract_full_text(pdf_bytes)
    txs = extract_bradesco_mensal(pdf_bytes)

    assert len(txs) > 1500
    credit = sum(tx.amount for tx in txs if tx.nature.value == "credito")
    debit = sum(tx.amount for tx in txs if tx.nature.value == "debito")
    assert round(credit, 2) == 1_296_806.46
    assert round(debit, 2) == 1_318_542.12

    result = validate_saldo(text, txs, get_bank_rules(BankCode.BRADESCO))
    assert result.saldo_inicial == 162_652.48
    assert result.saldo_final == 140_916.82
    assert result.ok is True
