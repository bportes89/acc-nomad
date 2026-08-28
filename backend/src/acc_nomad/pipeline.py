"""Pipeline principal ACC Nomad."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from acc_nomad.models import (
    BankCode,
    ProcessExtratoRequest,
    ProcessExtratoResponse,
    SaldoValidationResult,
    Transaction,
)
from acc_nomad.services.bank_detector import detect_bank_from_text
from acc_nomad.services.bank_rules import get_bank_rules
from acc_nomad.services.classifier import extract_and_classify
from acc_nomad.services.organizer import sort_transactions
from acc_nomad.services.pdf_analyzer import analyze_pdf, extract_full_text
from acc_nomad.services.fornecedor_matcher import FornecedorMatch, apply_fornecedor_categories
from acc_nomad.services.saldo_validator import validate_saldo
from acc_nomad.services.supabase_client import (
    SupabaseNotConfiguredError,
    fetch_fornecedores,
    fetch_plano_contas,
    save_transactions,
    update_extrato_status,
    update_extrato_saldo_validation,
)
from acc_nomad.services.transaction_utils import dedupe_transactions


class ProcessingError(RuntimeError):
    pass

_TEXT_CHUNK_CHARS = 18_000
_MAX_LLM_WORKERS = 3


def _split_text_for_llm(text: str, max_chars: int = _TEXT_CHUNK_CHARS) -> list[str]:
    """Divide texto longo em blocos para a LLM, cortando em quebras de linha."""
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        if end < len(cleaned):
            break_at = cleaned.rfind("\n", start, end)
            if break_at > start:
                end = break_at
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end if end > start else start + max_chars
    return chunks or [cleaned[:max_chars]]


def _extract_transactions(
    *,
    sample_text: str,
    bank: BankCode,
    segmento: str | None,
    instrucao_personalizada: str | None,
    fornecedores: list[FornecedorMatch],
    plano_contas: list[dict],
) -> list[Transaction]:
    text_parts = _split_text_for_llm(sample_text)
    if len(text_parts) == 1:
        return extract_and_classify(
            sample_text=text_parts[0],
            bank=bank,
            segmento=segmento,
            instrucao_personalizada=instrucao_personalizada,
            fornecedores=fornecedores,
            plano_contas=plano_contas,
        )

    all_transactions: list[Transaction] = []
    workers = min(_MAX_LLM_WORKERS, len(text_parts))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                extract_and_classify,
                text_part,
                bank,
                segmento,
                instrucao_personalizada,
                fornecedores,
                plano_contas,
            )
            for text_part in text_parts
        ]
        for future in as_completed(futures):
            all_transactions.extend(future.result())
    return all_transactions


def process_extrato_pdf(
    pdf_bytes: bytes,
    request: ProcessExtratoRequest,
) -> ProcessExtratoResponse:
    extrato_id = request.extrato_id

    try:
        update_extrato_status(extrato_id, status="processando")
    except SupabaseNotConfiguredError:
        raise ProcessingError(
            "Backend sem Supabase configurado. Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY "
            "no Render (Environment) ou em backend/.env (local)."
        ) from None

    try:
        analysis = analyze_pdf(pdf_bytes)
        bank = detect_bank_from_text(analysis.sample_text)
        bank_rules = get_bank_rules(bank)
        full_text = extract_full_text(pdf_bytes)

        raw_fornecedores = fetch_fornecedores(request.empresa_id)
        fornecedores = [
            FornecedorMatch(nome=f["nome"], categoria_sugerida=f.get("categoria_sugerida"))
            for f in raw_fornecedores
        ]

        plano_contas = fetch_plano_contas(request.segmento or "comercio")

        all_transactions = _extract_transactions(
            sample_text=full_text,
            bank=bank,
            segmento=request.segmento,
            instrucao_personalizada=request.instrucao_personalizada,
            fornecedores=fornecedores,
            plano_contas=plano_contas,
        )

        ordered = dedupe_transactions(all_transactions)
        ordered = sort_transactions(ordered, bank)
        ordered = apply_fornecedor_categories(ordered, fornecedores)

        if not ordered:
            raise ProcessingError(
                "Nenhum lançamento extraído do PDF. Verifique o arquivo ou configure "
                "ANTHROPIC_API_KEY com LLM_PROVIDER=anthropic no backend (Render)."
            )

        saldo_result = validate_saldo(full_text, ordered, bank_rules)

        save_transactions(
            extrato_id=extrato_id,
            empresa_id=request.empresa_id,
            transactions=ordered,
        )

        update_extrato_status(
            extrato_id,
            status="processado",
            banco=bank,
            total_lancamentos=len(ordered),
        )

        update_extrato_saldo_validation(
            extrato_id,
            saldo_inicial=saldo_result.saldo_inicial,
            saldo_final=saldo_result.saldo_final,
            saldo_calculado=saldo_result.saldo_calculado,
            validacao_saldo_ok=saldo_result.ok,
            validacao_detalhes=saldo_result.to_dict(),
        )

        return ProcessExtratoResponse(
            extrato_id=extrato_id,
            bank=bank,
            transactions=ordered,
            saldo_validation=SaldoValidationResult(**saldo_result.to_dict()),
        )
    except ProcessingError as exc:
        update_extrato_status(extrato_id, status="erro", erro_mensagem=str(exc))
        raise
    except Exception as exc:
        update_extrato_status(extrato_id, status="erro", erro_mensagem=str(exc))
        raise ProcessingError(str(exc)) from exc
