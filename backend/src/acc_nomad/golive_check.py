"""Critérios objetivos de GoLive — Item 7 + teste Bradesco."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from acc_nomad.models import BankCode
from acc_nomad.services.bank_detector import detect_bank_from_text
from acc_nomad.services.classifier import FALLBACK_CATEGORY, extract_and_classify
from acc_nomad.services.pdf_analyzer import analyze_pdf, extract_full_text_smart
from acc_nomad.services.reliable_extraction import extract_transactions_local
from acc_nomad.services.saldo_validator import validate_saldo
from acc_nomad.services.bank_rules import get_bank_rules
from acc_nomad.services.rule_classifier import classify_with_rules

# Limites comerciais (ajustáveis)
MAX_PROCESSING_SECONDS = 90
MIN_CLASSIFIED_RATIO = 0.70  # 70% fora de fallback
MIN_TX_PER_PAGE = 0.5  # ao menos ~1 lançamento a cada 2 páginas (extrato denso)


@dataclass
class GoLiveReport:
    pdf_path: str
    page_count: int
    bank: BankCode
    transaction_count: int
    classified_ratio: float
    saldo_ok: bool | None
    extract_seconds: float
    classify_seconds: float
    passed: bool
    failures: list[str]

    def to_dict(self) -> dict:
        return {
            "pdf_path": self.pdf_path,
            "page_count": self.page_count,
            "bank": self.bank.value,
            "transaction_count": self.transaction_count,
            "classified_ratio": round(self.classified_ratio, 3),
            "saldo_ok": self.saldo_ok,
            "extract_seconds": round(self.extract_seconds, 2),
            "classify_seconds": round(self.classify_seconds, 2),
            "passed": self.passed,
            "failures": self.failures,
        }


def run_golive_check(
    pdf_path: str | Path,
    *,
    segmento: str = "comercio",
    skip_llm: bool = False,
) -> GoLiveReport:
    path = Path(pdf_path)
    pdf_bytes = path.read_bytes()
    analysis = analyze_pdf(pdf_bytes, max_pages=3)
    bank = detect_bank_from_text(analysis.sample_text)
    bank_rules = get_bank_rules(bank)

    t0 = time.perf_counter()
    full_text = extract_full_text_smart(pdf_bytes).text
    t1 = time.perf_counter()

    local_txs: list = []
    t2 = t1

    if skip_llm:
        outcome = extract_transactions_local(
            pdf_bytes=pdf_bytes,
            full_text=full_text,
            bank=bank,
            default_category="Receita de vendas",
        )
        local_txs = outcome.transactions
        t2 = time.perf_counter()
        transactions = classify_with_rules(local_txs, default_receita="Receita de vendas")
    else:
        transactions = extract_and_classify(
            sample_text=full_text,
            bank=bank,
            segmento=segmento,
            plano_contas=None,
            pdf_bytes=pdf_bytes,
        )
    t3 = time.perf_counter()

    failures: list[str] = []
    page_count = max(analysis.page_count, 1)

    if len(full_text.strip()) < 500 and page_count > 3:
        failures.append(
            "PDF parece escaneado/imagem — pouco texto extraível (<500 chars). "
            "Precisa OCR ou PDF nativo."
        )

    if not transactions:
        failures.append("Nenhum lançamento extraído.")

    min_expected = int(page_count * MIN_TX_PER_PAGE)
    if len(transactions) < min_expected:
        failures.append(
            f"Poucos lançamentos ({len(transactions)}) para {page_count} páginas "
            f"(mínimo esperado: {min_expected})."
        )

    classified = [tx for tx in transactions if tx.category and tx.category != FALLBACK_CATEGORY]
    ratio = len(classified) / len(transactions) if transactions else 0.0
    if ratio < MIN_CLASSIFIED_RATIO:
        failures.append(
            f"Classificação insuficiente: {ratio:.0%} classificados "
            f"(mínimo {MIN_CLASSIFIED_RATIO:.0%})."
        )

    saldo = validate_saldo(full_text, transactions, bank_rules)
    saldo_ok: bool | None = saldo.ok if transactions else None
    if (
        saldo_ok is False
        and saldo.saldo_inicial is not None
        and saldo.saldo_final is not None
    ):
        failures.append(f"Divergência de saldo (delta R$ {saldo.delta}).")

    total_seconds = t3 - t0
    if total_seconds > MAX_PROCESSING_SECONDS:
        failures.append(
            f"Tempo total {total_seconds:.1f}s excede limite de {MAX_PROCESSING_SECONDS}s."
        )

    return GoLiveReport(
        pdf_path=str(path),
        page_count=page_count,
        bank=bank,
        transaction_count=len(transactions),
        classified_ratio=ratio,
        saldo_ok=saldo_ok,
        extract_seconds=t1 - t0,
        classify_seconds=t3 - t2,
        passed=len(failures) == 0,
        failures=failures,
    )
