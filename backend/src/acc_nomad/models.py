from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BankCode(str, Enum):
    BB = "bb"
    BRADESCO = "bradesco"
    SANTANDER = "santander"
    SICREDI = "sicredi"
    SICOOB = "sicoob"
    BASA = "basa"
    ITAU = "itau"
    UNICREDI = "unicredi"
    UNKNOWN = "unknown"


class TransactionNature(str, Enum):
    CREDIT = "credito"
    DEBIT = "debito"


class TransactionOrigin(str, Enum):
    BANK = "BANCO"
    TREASURY = "TESOURARIA"


class Transaction(BaseModel):
    date: date
    description: str
    amount: float
    nature: TransactionNature
    category: str | None = None
    origin: TransactionOrigin = TransactionOrigin.BANK
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessExtratoRequest(BaseModel):
    empresa_id: str
    extrato_id: str
    instrucao_personalizada: str | None = None
    segmento: str | None = None
    nome_arquivo: str = "extrato.pdf"


class SaldoValidationResult(BaseModel):
    ok: bool
    saldo_inicial: float | None = None
    saldo_final: float | None = None
    saldo_calculado: float | None = None
    delta: float | None = None
    warnings: list[str] = Field(default_factory=list)


class ProcessExtratoResponse(BaseModel):
    extrato_id: str
    bank: BankCode
    transactions: list[Transaction]
    status: str = "processed"
    saldo_validation: SaldoValidationResult | None = None
