"""Cálculo PMG a partir de dados do Supabase."""

from __future__ import annotations

from datetime import date

from acc_nomad.services.supabase_client import get_supabase_client

CATEGORIA_MAP: dict[str, str] = {
    "custo_variavel": "custo_variavel",
    "fornecedor": "custo_variavel",
    "fornecedor / revenda": "custo_variavel",
    "não classificado": "custo_variavel",
    "custo_fixo": "custo_fixo",
    "juros": "juros",
    "investimentos": "investimentos",
    "receita": "receita",
}


def _bucket_categoria(categoria: str, natureza: str) -> str:
    cat = categoria.lower()
    for key, bucket in CATEGORIA_MAP.items():
        if key in cat:
            return bucket
    return "receita" if natureza == "credito" else "custo_variavel"


def calcular_pmg_resumo(
    lancamentos: list[dict],
    tesouraria: list[dict],
) -> dict[str, float]:
    resumo = {
        "custo_variavel": 0.0,
        "custo_fixo": 0.0,
        "juros": 0.0,
        "investimentos": 0.0,
        "receita": 0.0,
    }

    for row in lancamentos:
        cat = row.get("categoria_corrigida") or row.get("categoria") or ""
        key = _bucket_categoria(str(cat), row.get("natureza", "debito"))
        resumo[key] += float(row.get("valor") or 0)

    for row in tesouraria:
        cat = row.get("categoria") or ""
        key = _bucket_categoria(str(cat), row.get("natureza", "debito"))
        resumo[key] += float(row.get("valor") or 0)

    return resumo


def fetch_pmg_data(
    empresa_id: str,
    periodo_inicio: date,
    periodo_fim: date,
) -> tuple[list[dict], list[dict]]:
    client = get_supabase_client()
    inicio = periodo_inicio.isoformat()
    fim = periodo_fim.isoformat()

    lancamentos = (
        client.table("lancamentos")
        .select("valor, natureza, categoria, categoria_corrigida, data")
        .eq("empresa_id", empresa_id)
        .gte("data", inicio)
        .lte("data", fim)
        .execute()
    )
    tesouraria = (
        client.table("tesouraria_lancamentos")
        .select("valor, natureza, categoria, data")
        .eq("empresa_id", empresa_id)
        .gte("data", inicio)
        .lte("data", fim)
        .execute()
    )

    return lancamentos.data or [], tesouraria.data or []
