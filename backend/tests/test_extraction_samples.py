from pathlib import Path

import pytest

from acc_nomad.services.bank_detector import detect_bank_from_text
from acc_nomad.services.pdf_analyzer import analyze_pdf, extract_full_text_smart
from acc_nomad.services.pdf_ocr import ocr_available
from acc_nomad.services.reliable_extraction import extract_transactions_local

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "EXTRATOS EXEMPLO"


def _sample_pdfs() -> list[Path]:
    if not SAMPLES_DIR.is_dir():
        return []
    return sorted(SAMPLES_DIR.glob("*.pdf"))


@pytest.mark.parametrize("pdf_path", _sample_pdfs(), ids=lambda p: p.name)
def test_local_extraction_saldo_matches_pdf(pdf_path: Path):
    pdf_bytes = pdf_path.read_bytes()
    text_extraction = extract_full_text_smart(pdf_bytes)
    full_text = text_extraction.text
    if len(full_text.strip()) < 300 and not text_extraction.used_ocr:
        if not ocr_available():
            pytest.skip(f"{pdf_path.name}: PDF escaneado — OCR indisponível neste ambiente")
        pytest.skip(f"{pdf_path.name}: OCR não extraiu texto suficiente")

    analysis = analyze_pdf(pdf_bytes, max_pages=3)
    bank = detect_bank_from_text(analysis.sample_text)

    outcome = extract_transactions_local(
        pdf_bytes=pdf_bytes,
        full_text=full_text,
        bank=bank,
    )

    assert outcome.transactions, f"Nenhum lançamento extraído de {pdf_path.name}"
    saldo = outcome.saldo
    if saldo.saldo_inicial is not None and saldo.saldo_final is not None:
        assert saldo.ok is True, (
            f"{pdf_path.name}: delta R$ {saldo.delta} "
            f"(calc {saldo.saldo_calculado} vs pdf {saldo.saldo_final}) "
            f"via {outcome.strategy}"
        )
