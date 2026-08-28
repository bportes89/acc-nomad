"""Pipeline principal ACC Nomad."""

from __future__ import annotations

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
from acc_nomad.services.pdf_analyzer import analyze_pdf, extract_full_text_smart
from acc_nomad.services.pdf_ocr import MIN_NATIVE_TEXT_CHARS, is_scanned_pdf, ocr_available
from acc_nomad.services.fornecedor_matcher import FornecedorMatch, apply_fornecedor_categories
from acc_nomad.services.reliable_extraction import extract_transactions_local
from acc_nomad.services.saldo_validator import validate_saldo
from acc_nomad.services.supabase_client import (
    SupabaseNotConfiguredError,
    fetch_fornecedores,
    fetch_plano_contas,
    save_transactions,
    update_extrato_status,
    update_extrato_saldo_validation,
)


class ProcessingError(RuntimeError):
    pass


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
        text_extraction = extract_full_text_smart(pdf_bytes)
        full_text = text_extraction.text

        raw_fornecedores = fetch_fornecedores(request.empresa_id)
        fornecedores = [
            FornecedorMatch(nome=f["nome"], categoria_sugerida=f.get("categoria_sugerida"))
            for f in raw_fornecedores
        ]

        plano_contas = fetch_plano_contas(request.segmento or "comercio")

        all_transactions: list[Transaction] = extract_and_classify(
            sample_text=full_text,
            bank=bank,
            segmento=request.segmento,
            instrucao_personalizada=request.instrucao_personalizada,
            fornecedores=fornecedores,
            plano_contas=plano_contas,
            pdf_bytes=pdf_bytes,
        )

        ordered = sort_transactions(all_transactions, bank)
        ordered = apply_fornecedor_categories(ordered, fornecedores)

        if not ordered:
            if is_scanned_pdf(pdf_bytes) and not text_extraction.used_ocr:
                if not ocr_available():
                    raise ProcessingError(
                        "PDF escaneado ou imagem — texto não selecionável. "
                        "O servidor ainda não tem OCR (Tesseract) ativo. "
                        "Baixe o extrato em PDF nativo pelo internet banking."
                    )
                raise ProcessingError(
                    "PDF escaneado — OCR não conseguiu ler o conteúdo. "
                    "Tente um PDF nativo ou um scan com melhor qualidade."
                )
            if len(full_text.strip()) < MIN_NATIVE_TEXT_CHARS:
                raise ProcessingError(
                    "PDF sem texto selecionável (escaneado ou imagem). "
                    "Baixe o extrato pelo internet banking em PDF nativo, não foto/scan."
                )
            raise ProcessingError(
                f"Nenhum lançamento extraído do PDF (banco detectado: {bank.value}). "
                "Formato ainda não reconhecido — abra Suporte e anexe o arquivo para análise."
            )

        saldo_result = validate_saldo(full_text, ordered, bank_rules)

        if (
            saldo_result.saldo_inicial is not None
            and saldo_result.saldo_final is not None
            and not saldo_result.ok
        ):
            saldo_result.warnings.append(
                "Extrato salvo para revisão: saldo calculado não fecha com o PDF. "
                "Confira lançamentos antes de enviar ao PMG."
            )

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
            validacao_detalhes={
                **saldo_result.to_dict(),
                "used_ocr": text_extraction.used_ocr,
            },
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
        raise ProcessingError(
            "Erro interno ao processar o extrato. Tente novamente ou abra um report em Suporte."
        ) from exc
