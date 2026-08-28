"""Classificação heurística rápida — reduz dependência da LLM."""

from __future__ import annotations

import re

from acc_nomad.models import Transaction, TransactionNature

FALLBACK_CATEGORY = "Não classificado (fallback)"

# (padrões na descrição, categoria, natureza opcional)
_KEYWORD_RULES: list[tuple[tuple[str, ...], str, TransactionNature | None]] = [
    (("TARIFA", "TAXA", "IOF", "PACOTE DE SERV", "MANUT CONTA", "ANUIDADE"), "Multas / Tarifas", None),
    (("JUROS", "MORA", "ENCARGOS"), "Juros bancários", None),
    (("PIX RECEB", "PIX-RECEB", "TED-CR", "TED CR", "CREDITO EM CONTA", "DEP CHQ", "DEPOSITO"), "Receita de vendas", TransactionNature.CREDIT),
    (("RECEBIMENTO", "RECEBIMENTO PIX", "VENDA"), "Receita de vendas", TransactionNature.CREDIT),
    (("SALARIO", "SALÁRIO", "FOLHA", "PROLABORE"), "Salários", TransactionNature.DEBIT),
    (("ALUGUEL", "LOCACAO", "LOCAÇÃO"), "Aluguel", TransactionNature.DEBIT),
    (("ENERGIA", "CEMIG", "CPFL", "LIGHT", "AGUA", "ÁGUA", "INTERNET", "VIVO", "CLARO", "TIM"), "Energia / Água / Internet", TransactionNature.DEBIT),
    (("CONTABIL", "CONTADOR"), "Contabilidade", TransactionNature.DEBIT),
    (("FORNECEDOR", "COMPRA", "NF ", "NOTA FISCAL"), "Fornecedor / Revenda", TransactionNature.DEBIT),
    (("INVEST", "APLICAC", "CDB", "LCI", "LCA"), "Investimentos", None),
    (("SAQUE", "PAGAMENTO", "DEBITO", "DÉBITO", "ENVIO PIX", "PIX ENVIAD"), "Fornecedor / Revenda", TransactionNature.DEBIT),
]

_UBER_RE = re.compile(r"\bUBER\b", re.I)
_NUBANK_RE = re.compile(r"\bNU PAGAMENTOS\b", re.I)


def classify_with_rules(
    transactions: list[Transaction],
    *,
    default_receita: str | None = None,
) -> list[Transaction]:
    updated: list[Transaction] = []
    for tx in transactions:
        if tx.category and tx.category != FALLBACK_CATEGORY:
            updated.append(tx)
            continue

        category = _match_category(tx, default_receita=default_receita)
        if category:
            updated.append(tx.model_copy(update={"category": category}))
        else:
            updated.append(tx)
    return updated


def _match_category(tx: Transaction, *, default_receita: str | None) -> str | None:
    upper = tx.description.upper()

    if tx.nature == TransactionNature.CREDIT and default_receita:
        if any(k in upper for k in ("PIX", "TED", "CREDITO", "CRÉDITO", "DEP ", "RECEB")):
            return default_receita

    if _UBER_RE.search(tx.description):
        return "Fornecedor / Revenda"

    for keywords, category, nature in _KEYWORD_RULES:
        if nature is not None and tx.nature != nature:
            continue
        if any(k in upper for k in keywords):
            return category

    if tx.nature == TransactionNature.CREDIT and default_receita:
        return default_receita

    return None
