"""Extração e classificação via LLM configurável (Gemini, Groq, etc.)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from acc_nomad.models import BankCode, Transaction, TransactionNature
from acc_nomad.services.bank_rules import BankRules, get_bank_rules
from acc_nomad.services.fallback_extractor import extract_all_local, filter_transaction_candidate_lines
from acc_nomad.services.fornecedor_matcher import FornecedorMatch, apply_fornecedor_categories
from acc_nomad.services.llm_providers import active_provider_name, generate_json, generate_json_fast
from acc_nomad.services.reliable_extraction import extract_transactions_local
from acc_nomad.services.rule_classifier import classify_with_rules
from acc_nomad.services.transaction_utils import prepare_transactions

DEFAULT_CATEGORIES = [
    ("Fornecedor / Revenda", "custo variável"),
    ("Matéria-prima", "custo variável"),
    ("Aluguel", "custo fixo"),
    ("Salários", "custo fixo"),
    ("Energia / Água / Internet", "custo fixo"),
    ("Contabilidade", "custo fixo"),
    ("Juros bancários", "juros"),
    ("Multas / Tarifas", "juros"),
    ("Investimentos", "investimentos"),
    ("Receita de vendas", "receita"),
    ("Outras receitas", "receita"),
]

CATEGORIA_PAI_LABELS = {
    "custo_variavel": "custo variável",
    "custo_fixo": "custo fixo",
    "juros": "juros",
    "investimentos": "investimentos",
    "receita": "receita",
}

FALLBACK_CATEGORY = "Não classificado (fallback)"

EXTRACTION_PROMPT_BASE = """Você é um assistente contábil da ACC/Nomad.
Extraia lançamentos bancários do texto fornecido e classifique cada um no plano de contas.

Use EXCLUSIVAMENTE estas categorias do plano de contas ({segmento}):
{categorias}

Retorne JSON:
{{
  "transactions": [
    {{
      "date": "YYYY-MM-DD",
      "description": "texto",
      "amount": 123.45,
      "nature": "credito" | "debito",
      "category": "categoria exata do plano de contas"
    }}
  ]
}}

Regras:
- amount sempre positivo; nature indica crédito ou débito
- Use fornecedores cadastrados quando o nome aparecer na descrição
- Respeite instruções personalizadas
- Não invente lançamentos ausentes no texto
- category deve ser o nome exato de uma categoria listada acima
- Retorne APENAS JSON válido (sem markdown). Descrições curtas.
"""

CLASSIFY_BATCH_PROMPT = """Você classifica lançamentos bancários no plano de contas ({segmento}).

Categorias permitidas:
{categorias}

Retorne JSON: {{"items": [{{"i": 0, "category": "nome exato"}}, ...]}}
- i = índice do item na lista enviada
- category deve ser nome exato de uma categoria acima
- Apenas JSON, sem markdown
"""


def _format_plano_contas(plano_contas: list[dict[str, Any]] | None) -> list[tuple[str, str]]:
    if not plano_contas:
        return DEFAULT_CATEGORIES

    formatted: list[tuple[str, str]] = []
    for item in plano_contas:
        pai = CATEGORIA_PAI_LABELS.get(item.get("categoria_pai") or "", "outros")
        formatted.append((item["nome"], pai))
    return formatted or DEFAULT_CATEGORIES


def _build_extraction_prompt(
    segmento: str | None,
    plano_contas: list[dict[str, Any]] | None,
    bank_rules: BankRules | None = None,
) -> str:
    categorias = _format_plano_contas(plano_contas)
    categorias_txt = "\n".join(f"- {nome} ({pai})" for nome, pai in categorias)
    bank_section = ""
    if bank_rules:
        bank_section = (
            f"\nRegras do banco ({bank_rules.label}):\n"
            f"- Formato de data: {bank_rules.date_format_hint}\n"
            f"- Natureza: indicador {bank_rules.nature_strategy}\n"
            f"- {bank_rules.extraction_hints}\n"
        )
    return EXTRACTION_PROMPT_BASE.format(
        segmento=segmento or "comercio",
        categorias=categorias_txt,
    ) + bank_section


def _build_classify_prompt(
    segmento: str | None,
    plano_contas: list[dict[str, Any]] | None,
) -> str:
    categorias = _format_plano_contas(plano_contas)
    categorias_txt = "\n".join(f"- {nome} ({pai})" for nome, pai in categorias)
    return CLASSIFY_BATCH_PROMPT.format(
        segmento=segmento or "comercio",
        categorias=categorias_txt,
    )


def _default_receita_category(plano_contas: list[dict[str, Any]] | None) -> str | None:
    if not plano_contas:
        return None
    for item in plano_contas:
        if item.get("categoria_pai") == "receita":
            return item["nome"]
    return None


def _needs_classification(tx: Transaction) -> bool:
    return not tx.category or tx.category == FALLBACK_CATEGORY


def extract_and_classify(
    sample_text: str,
    bank: BankCode,
    segmento: str | None = None,
    instrucao_personalizada: str | None = None,
    fornecedores: list[FornecedorMatch] | None = None,
    plano_contas: list[dict[str, Any]] | None = None,
    pdf_bytes: bytes | None = None,
) -> list[Transaction]:
    fornecedores = fornecedores or []
    receita_default = _default_receita_category(plano_contas)
    rules = get_bank_rules(bank)
    transactions: list[Transaction] = []

    if pdf_bytes:
        outcome = extract_transactions_local(
            pdf_bytes=pdf_bytes,
            full_text=sample_text,
            bank=bank,
            default_category=receita_default,
        )
        transactions = outcome.transactions

    if not transactions:
        transactions = extract_all_local(sample_text, default_category=receita_default)
        transactions = prepare_transactions(transactions, sample_text, rules)

    if transactions:
        transactions = apply_fornecedor_categories(transactions, fornecedores)
        transactions = classify_with_rules(transactions, default_receita=receita_default)
        return _classify_batch(
            transactions,
            segmento=segmento,
            instrucao_personalizada=instrucao_personalizada,
            plano_contas=plano_contas,
        )

    if active_provider_name() == "fallback":
        return []

    llm_txs = _extract_with_full_llm(
        sample_text=sample_text,
        bank=bank,
        segmento=segmento,
        instrucao_personalizada=instrucao_personalizada,
        fornecedores=fornecedores,
        plano_contas=plano_contas,
    )
    return prepare_transactions(llm_txs, sample_text, rules)


def _classify_batch(
    transactions: list[Transaction],
    *,
    segmento: str | None,
    instrucao_personalizada: str | None,
    plano_contas: list[dict[str, Any]] | None,
) -> list[Transaction]:
    if active_provider_name() == "fallback":
        return transactions

    pending = [i for i, tx in enumerate(transactions) if _needs_classification(tx)]
    if not pending:
        return transactions

    prompt = _build_classify_prompt(segmento, plano_contas)
    batch_size = 80

    for start in range(0, len(pending), batch_size):
        batch_indices = pending[start : start + batch_size]
        payload_items = [
            {
                "i": idx,
                "desc": transactions[idx].description[:100],
                "nat": transactions[idx].nature.value,
            }
            for idx in batch_indices
        ]
        user_content = json.dumps(
            {
                "instrucao_personalizada": instrucao_personalizada or "nenhuma",
                "items": payload_items,
            },
            ensure_ascii=False,
        )
        result = generate_json_fast(prompt, user_content)
        for item in result.get("items", []):
            try:
                idx = int(item["i"])
                category = str(item["category"]).strip()
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= idx < len(transactions) and category:
                tx = transactions[idx]
                transactions[idx] = tx.model_copy(update={"category": category})

    return transactions


def _extract_with_full_llm(
    *,
    sample_text: str,
    bank: BankCode,
    segmento: str | None,
    instrucao_personalizada: str | None,
    fornecedores: list[FornecedorMatch],
    plano_contas: list[dict[str, Any]] | None,
) -> list[Transaction]:
    """Caminho lento — só quando regex não extrai nada (PDF escaneado/imagem)."""
    bank_rules = get_bank_rules(bank or BankCode.UNKNOWN)
    prompt = _build_extraction_prompt(segmento, plano_contas, bank_rules)
    receita_default = _default_receita_category(plano_contas)

    fornecedores_txt = "\n".join(
        f"- {f.nome} → {f.categoria_sugerida or 'sem categoria'}" for f in fornecedores
    ) or "Nenhum fornecedor cadastrado."

    compact = filter_transaction_candidate_lines(sample_text)
    text_for_llm = compact if len(compact) >= 80 else sample_text[:25000]

    user_content = (
        f"Banco: {bank.value}\n"
        f"Segmento: {segmento or 'comercio'}\n"
        f"Instrução personalizada: {instrucao_personalizada or 'nenhuma'}\n\n"
        f"Fornecedores cadastrados:\n{fornecedores_txt}\n\n"
        f"Texto do extrato:\n{text_for_llm[:25000]}"
    )

    payload = generate_json(prompt, user_content, max_tokens=8192)

    transactions: list[Transaction] = []
    for item in payload.get("transactions", []):
        try:
            transactions.append(_to_transaction(item))
        except (KeyError, ValueError, TypeError):
            continue

    if transactions:
        return apply_fornecedor_categories(transactions, fornecedores)

    txs = extract_all_local(sample_text, default_category=receita_default)
    return apply_fornecedor_categories(txs, fornecedores)


def _to_transaction(item: dict) -> Transaction:
    return Transaction(
        date=date.fromisoformat(item["date"]),
        description=item.get("description", "").strip(),
        amount=float(item.get("amount", 0)),
        nature=TransactionNature(item.get("nature", "debito")),
        category=item.get("category"),
    )
