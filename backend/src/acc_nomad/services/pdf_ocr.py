"""OCR de PDFs escaneados via Tesseract (PyMuPDF)."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import pymupdf as fitz

logger = logging.getLogger(__name__)

MIN_NATIVE_TEXT_CHARS = 300
DEFAULT_OCR_DPI = 200
DEFAULT_OCR_LANGUAGE = "por"

_TESSDATA_CANDIDATES = (
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tesseract-ocr/tessdata",
    "C:/Program Files/Tesseract-OCR/tessdata",
)

_tesseract_configured: bool | None = None
_ocr_supported: bool | None = None


def _configure_tesseract() -> bool:
    global _tesseract_configured
    if _tesseract_configured is not None:
        return _tesseract_configured

    prefix = os.environ.get("TESSDATA_PREFIX", "").strip()
    if prefix and _has_tessdata(prefix):
        _tesseract_configured = True
        return True

    for candidate in _TESSDATA_CANDIDATES:
        if _has_tessdata(candidate):
            os.environ["TESSDATA_PREFIX"] = candidate
            if hasattr(fitz, "TESSDATA_PREFIX"):
                fitz.TESSDATA_PREFIX = candidate
            logger.info("TESSDATA_PREFIX configurado: %s", candidate)
            _tesseract_configured = True
            return True

    _tesseract_configured = False
    return False


def _has_tessdata(prefix: str) -> bool:
    base = Path(prefix)
    return (base / "eng.traineddata").is_file() or (base / "por.traineddata").is_file()


def ocr_available() -> bool:
    """True se tessdata do Tesseract está configurado."""
    global _ocr_supported
    if _ocr_supported is not None:
        return _ocr_supported

    _ocr_supported = _configure_tesseract()
    return _ocr_supported


def is_scanned_pdf(pdf_bytes: bytes, *, min_chars: int = MIN_NATIVE_TEXT_CHARS) -> bool:
    """Heurística: pouco texto nativo em PDF multi-página ou página única."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        native = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    return len(native.strip()) < min_chars


def ocr_page_text(
    page: fitz.Page,
    *,
    dpi: int = DEFAULT_OCR_DPI,
    language: str = DEFAULT_OCR_LANGUAGE,
) -> str:
    if not ocr_available():
        return page.get_text()
    try:
        tp = page.get_textpage_ocr(dpi=dpi, full=True, language=language)
        return page.get_text(textpage=tp)
    except Exception as exc:
        logger.warning("Falha OCR na página %s: %s", page.number + 1, exc)
        return page.get_text()


def extract_text_ocr(
    pdf_bytes: bytes,
    *,
    dpi: int = DEFAULT_OCR_DPI,
    language: str = DEFAULT_OCR_LANGUAGE,
    max_pages: int | None = None,
) -> str:
    """OCR de todas as páginas (ou limite) do PDF."""
    if not ocr_available():
        raise RuntimeError(
            "OCR indisponível. Instale Tesseract e os pacotes de idioma (por/eng)."
        )

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    parts: list[str] = []
    try:
        limit = len(doc) if max_pages is None else min(len(doc), max_pages)
        for index in range(limit):
            parts.append(
                ocr_page_text(doc[index], dpi=dpi, language=language)
            )
    finally:
        doc.close()

    return "\n".join(parts)


def tesseract_version() -> str | None:
    if not _configure_tesseract():
        return None
    return shutil.which("tesseract")
