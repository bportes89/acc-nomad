"""Match de fornecedores cadastrados na descrição do lançamento."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FornecedorMatch:
    nome: str
    categoria_sugerida: str | None


def match_fornecedor(descricao: str, fornecedores: list[FornecedorMatch]) -> str | None:
    desc_lower = descricao.lower()
    for f in sorted(fornecedores, key=lambda x: len(x.nome), reverse=True):
        if f.nome.lower() in desc_lower and f.categoria_sugerida:
            return f.categoria_sugerida
    return None


def apply_fornecedor_categories(
    transactions: list,
    fornecedores: list[FornecedorMatch],
) -> list:
    for tx in transactions:
        if tx.category and tx.category != "Não classificado (fallback)":
            continue
        matched = match_fornecedor(tx.description, fornecedores)
        if matched:
            tx.category = matched
    return transactions
