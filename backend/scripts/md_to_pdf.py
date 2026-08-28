#!/usr/bin/env python3
"""Converte docs/GUIA-ENTREGA-E-TESTES.md para PDF."""

from __future__ import annotations

import sys
from pathlib import Path

import markdown
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "docs" / "GUIA-ENTREGA-E-TESTES.md"
PDF_PATH = ROOT / "docs" / "GUIA-ENTREGA-E-TESTES.pdf"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <title>ACC Nomad — Guia de entrega e testes</title>
  <style>
    @page {{
      size: A4;
      margin: 2cm 1.8cm;
    }}
    body {{
      font-family: Helvetica, Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.45;
      color: #1e293b;
    }}
    h1 {{
      font-size: 20pt;
      color: #0f172a;
      border-bottom: 2px solid #059669;
      padding-bottom: 8px;
      margin-top: 0;
    }}
    h2 {{
      font-size: 14pt;
      color: #0f172a;
      margin-top: 22px;
      page-break-after: avoid;
    }}
    h3 {{
      font-size: 11pt;
      color: #334155;
      margin-top: 16px;
      page-break-after: avoid;
    }}
    p, li {{
      margin: 6px 0;
    }}
    code {{
      font-family: Courier, monospace;
      font-size: 8.5pt;
      background: #f1f5f9;
      padding: 1px 4px;
    }}
    pre {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 10px;
      font-size: 8pt;
      line-height: 1.35;
      white-space: pre-wrap;
      word-wrap: break-word;
    }}
    pre code {{
      background: transparent;
      padding: 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9pt;
      margin: 10px 0;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f1f5f9;
      font-weight: bold;
    }}
    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 20px 0;
    }}
    a {{
      color: #059669;
      text-decoration: none;
    }}
    blockquote {{
      border-left: 3px solid #059669;
      margin: 10px 0;
      padding: 4px 12px;
      color: #475569;
    }}
    ul, ol {{
      padding-left: 20px;
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def main() -> None:
    if not MD_PATH.is_file():
        print(f"Arquivo não encontrado: {MD_PATH}", file=sys.stderr)
        sys.exit(1)

    md_text = MD_PATH.read_text(encoding="utf-8")
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    html = HTML_TEMPLATE.format(body=body)

    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PDF_PATH.open("wb") as pdf_file:
        status = pisa.CreatePDF(html.encode("utf-8"), dest=pdf_file, encoding="utf-8")

    if status.err:
        print(f"Erro ao gerar PDF (código {status.err})", file=sys.stderr)
        sys.exit(1)

    size_kb = PDF_PATH.stat().st_size // 1024
    print(f"PDF gerado: {PDF_PATH} ({size_kb} KB)")


if __name__ == "__main__":
    main()
