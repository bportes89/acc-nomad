"""Extração e classificação via LLM configurável (Gemini, Groq, etc.)."""

from __future__ import annotations

from datetime import date
from typing import Any

from acc_nomad.models import BankCode, Transaction, TransactionNature
from acc_nomad.services.bank_rules import BankRules, get_bank_rules
from acc_nomad.services.fallback_extractor import extract_fallback
from acc_nomad.services.fornecedor_matcher import FornecedorMatch, apply_fornecedor_categories
from acc_nomad.services.llm_providers import LlmCallError, active_provider_name, generate_json

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


def _default_receita_category(plano_contas: list[dict[str, Any]] | None) -> str | None:
    if not plano_contas:
        return None
    for item in plano_contas:
        if item.get("categoria_pai") == "receita":
            return item["nome"]
    return None


def extract_and_classify(
    sample_text: str,
    bank: BankCode,
    segmento: str | None = None,
    instrucao_personalizada: str | None = None,
    fornecedores: list[FornecedorMatch] | None = None,
    plano_contas: list[dict[str, Any]] | None = None,
) -> list[Transaction]:
    fornecedores = fornecedores or []
    bank_rules = get_bank_rules(bank or BankCode.UNKNOWN)
    prompt = _build_extraction_prompt(segmento, plano_contas, bank_rules)
    receita_default = _default_receita_category(plano_contas)

    if active_provider_name() == "fallback":
        txs = extract_fallback(sample_text, default_category=receita_default)
        return apply_fornecedor_categories(txs, fornecedores)

    fornecedores_txt = "\n".join(
        f"- {f.nome} → {f.categoria_sugerida or 'sem categoria'}" for f in fornecedores
    ) or "Nenhum fornecedor cadastrado."

    user_content = (
        f"Banco: {bank.value}\n"
        f"Segmento: {segmento or 'comercio'}\n"
        f"Instrução personalizada: {instrucao_personalizada or 'nenhuma'}\n\n"
        f"Fornecedores cadastrados:\n{fornecedores_txt}\n\n"
        f"Texto do extrato:\n{sample_text[:12000]}"
    )

    try:
        payload = generate_json(prompt, user_content)
    except LlmCallError as exc:
        raise RuntimeError(str(exc)) from exc

    transactions = [_to_transaction(item) for item in payload.get("transactions", [])]

    if transactions:
        return apply_fornecedor_categories(transactions, fornecedores)

    txs = extract_fallback(sample_text, default_category=receita_default)
    return apply_fornecedor_categories(txs, fornecedores)


def _to_transaction(item: dict) -> Transaction:
    return Transaction(
        date=date.fromisoformat(item["date"]),
        description=item.get("description", "").strip(),
        amount=float(item.get("amount", 0)),
        nature=TransactionNature(item.get("nature", "debito")),
        category=item.get("category"),
    )
