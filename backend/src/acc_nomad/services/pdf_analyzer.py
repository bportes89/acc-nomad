"""Análise visual do PDF — substitui nó PDFlib do n8n."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pymupdf as fitz


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


def extract_full_text(pdf_bytes: bytes, max_chars: int = 80000) -> str:
    """Texto completo do PDF para validação de saldos."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        parts = [page.get_text() for page in doc]
        return "\n".join(parts)[:max_chars]
    finally:
        doc.close()
