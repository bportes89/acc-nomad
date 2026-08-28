"""Regras de negócio por banco — porte simplificado do n8n Switch + PDFlib."""

from __future__ import annotations

from dataclasses import dataclass, field

from acc_nomad.models import BankCode


@dataclass(frozen=True)
class BankRules:
    bank: BankCode
    label: str
    sort_reverse: bool = False
    date_format_hint: str = "DD/MM/YYYY"
    nature_strategy: str = "cd_letter"
    saldo_anterior_keywords: tuple[str, ...] = ("SALDO ANTERIOR", "SALDO ANTER")
    saldo_final_keywords: tuple[str, ...] = ("SALDO FINAL", "SALDO ATUAL", "SALDO DO DIA")
    skip_keywords: tuple[str, ...] = ()
    extraction_hints: str = ""


COMMON_SKIP = (
    "LIMITE ESPECIAL",
    "TAXA ",
    "CUSTO EFETIVO",
    "INFORMAC",
    "OBSERV",
    "SAC ",
    "OUVIDORIA",
    "S A L D O",
)

RULES: dict[BankCode, BankRules] = {
    BankCode.BB: BankRules(
        bank=BankCode.BB,
        label="Banco do Brasil",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints=(
            "Extrato BB: datas DD/MM/YYYY; valores com sufixo C (crédito) ou D (débito); "
            "ignore linhas de saldo e tarifas informativas."
        ),
    ),
    BankCode.BRADESCO: BankRules(
        bank=BankCode.BRADESCO,
        label="Bradesco",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints=(
            "Extrato Bradesco: multi-página; colunas Data | Histórico | Valor; "
            "C/D ou sinal indica natureza; saldo anterior no cabeçalho."
        ),
    ),
    BankCode.SANTANDER: BankRules(
        bank=BankCode.SANTANDER,
        label="Santander",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints=(
            "Extrato Santander: datas DD/MM/YYYY; movimentações com coluna de valor "
            "e indicador C/D ou crédito/débito."
        ),
    ),
    BankCode.ITAU: BankRules(
        bank=BankCode.ITAU,
        label="Itaú",
        sort_reverse=True,
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints=(
            "Extrato Itaú: lançamentos costumam vir em ordem DECRESCENTE de data — "
            "extraia todos e mantenha datas corretas; C/D indica natureza."
        ),
    ),
    BankCode.SICREDI: BankRules(
        bank=BankCode.SICREDI,
        label="Sicredi",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints=(
            "Extrato Sicredi: cooperativa; valores terminam com C ou D; "
            "PIX e TED aparecem no histórico."
        ),
    ),
    BankCode.SICOOB: BankRules(
        bank=BankCode.SICOOB,
        label="Sicoob",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints=(
            "Extrato Sicoob: cooperativa; formato similar ao Sicredi; "
            "valores com C (entrada) ou D (saída) ao final da linha."
        ),
    ),
    BankCode.BASA: BankRules(
        bank=BankCode.BASA,
        label="Basa",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints="Extrato Basa (Banco da Amazônia): datas DD/MM/YYYY; C/D para natureza.",
    ),
    BankCode.UNICREDI: BankRules(
        bank=BankCode.UNICREDI,
        label="Unicredi",
        date_format_hint="DD/MM/YYYY",
        nature_strategy="cd_letter",
        extraction_hints="Extrato Unicredi: cooperativa; C/D indica crédito/débito.",
    ),
    BankCode.UNKNOWN: BankRules(
        bank=BankCode.UNKNOWN,
        label="Desconhecido",
        extraction_hints=(
            "Banco não identificado: use datas DD/MM/YYYY e inferir crédito/débito "
            "por C/D, sinal ou coluna."
        ),
    ),
}


def get_bank_rules(bank: BankCode) -> BankRules:
    return RULES.get(bank, RULES[BankCode.UNKNOWN])


def all_skip_keywords(bank: BankCode) -> tuple[str, ...]:
    rules = get_bank_rules(bank)
    return tuple(dict.fromkeys([*COMMON_SKIP, *rules.skip_keywords]))
