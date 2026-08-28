"""Análise visual do PDF — substitui nó PDFlib do n8n."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pymupdf as fitz

from acc_nomad.services.pdf_ocr import (
    MIN_NATIVE_TEXT_CHARS,
    extract_text_ocr,
    is_scanned_pdf,
    ocr_available,
    ocr_page_text,
)


@dataclass
class PdfTextExtraction:
    text: str
    used_ocr: bool


@dataclass
class PdfPageLayout:
    page_number: int
    text_blocks: list[dict]
    width: float
    height: float


@dataclass
class PdfVisualAnalysis:
    page_count: int
    pages: list[PdfPageLayout]
    sample_text: str


def analyze_pdf(pdf_bytes: bytes, max_pages: int = 3) -> PdfVisualAnalysis:
    """Extrai layout e texto inicial para detecção de banco e crédito/débito."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[PdfPageLayout] = []
    sample_parts: list[str] = []

    try:
        for index, page in enumerate(doc):
            if index >= max_pages:
                break

            blocks = []
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        blocks.append(
                            {
                                "text": text,
                                "x0": span["bbox"][0],
                                "y0": span["bbox"][1],
                                "x1": span["bbox"][2],
                                "y1": span["bbox"][3],
                                "color": span.get("color"),
                            }
                        )

            pages.append(
                PdfPageLayout(
                    page_number=index + 1,
                    text_blocks=blocks,
                    width=page.rect.width,
                    height=page.rect.height,
                )
            )
            sample_parts.append(page.get_text())
            if len(sample_parts[-1].strip()) < 20 and ocr_available():
                sample_parts[-1] = ocr_page_text(page)

        return PdfVisualAnalysis(
            page_count=len(doc),
            pages=pages,
            sample_text="\n".join(sample_parts)[:8000],
        )
    finally:
        doc.close()


def chunk_pdf_pages(pdf_bytes: bytes, chunk_size: int = 5) -> list[bytes]:
    """Divide extrato grande em chunks, sempre incluindo a 1ª página."""
    source = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunks: list[bytes] = []

    try:
        total = len(source)
        if total <= chunk_size:
            return [pdf_bytes]

        first_page = fitz.open()
        first_page.insert_pdf(source, from_page=0, to_page=0)

        for start in range(1, total, chunk_size):
            chunk_doc = fitz.open()
            chunk_doc.insert_pdf(first_page)
            end = min(start + chunk_size - 1, total - 1)
            chunk_doc.insert_pdf(source, from_page=start, to_page=end)
            buffer = io.BytesIO()
            chunk_doc.save(buffer)
            chunks.append(buffer.getvalue())
            chunk_doc.close()

        first_page.close()
        return chunks
    finally:
        source.close()


def extract_full_text(pdf_bytes: bytes, max_chars: int = 250_000) -> str:
    """Texto completo do PDF para extração e validação de saldos."""
    return extract_full_text_smart(pdf_bytes, max_chars=max_chars).text


def extract_full_text_smart(
    pdf_bytes: bytes,
    max_chars: int = 250_000,
) -> PdfTextExtraction:
    """Texto nativo; se escaneado, aplica OCR (Tesseract)."""
    native = _extract_native_text(pdf_bytes, max_chars=max_chars)
    if len(native.strip()) >= MIN_NATIVE_TEXT_CHARS:
        return PdfTextExtraction(text=native, used_ocr=False)

    if not ocr_available():
        return PdfTextExtraction(text=native, used_ocr=False)

    try:
        ocr_text = extract_text_ocr(pdf_bytes)
    except RuntimeError:
        return PdfTextExtraction(text=native, used_ocr=False)

    cleaned = ocr_text.strip()
    if len(cleaned) <= len(native.strip()):
        return PdfTextExtraction(text=native, used_ocr=False)

    return PdfTextExtraction(
        text=_truncate_text(cleaned, max_chars),
        used_ocr=True,
    )


def _extract_native_text(pdf_bytes: bytes, max_chars: int = 250_000) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        parts = [page.get_text() for page in doc]
        full = "\n".join(parts)
        return _truncate_text(full, max_chars)
    finally:
        doc.close()


def _truncate_text(full: str, max_chars: int) -> str:
    if len(full) <= max_chars:
        return full
    lines = full.splitlines()
    if len(lines) <= 8:
        return full[:max_chars]
    head = "\n".join(lines[:4])
    tail = "\n".join(lines[-4:])
    merged = f"{head}\n...\n{tail}"
    return merged if len(merged) <= max_chars else full[:max_chars]
