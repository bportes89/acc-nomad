"""Diagnóstico de divergência de saldo — extrato Bradesco mensal."""

from __future__ import annotations

import sys
from pathlib import Path

from acc_nomad.models import BankCode
from acc_nomad.services.bank_rules import get_bank_rules
from acc_nomad.services.bradesco_mensal_extractor import extract_bradesco_mensal
from acc_nomad.services.pdf_analyzer import extract_full_text
from acc_nomad.services.saldo_validator import validate_saldo
from acc_nomad.services.transaction_utils import dedupe_transactions


def main(pdf_path: Path) -> None:
    pdf_bytes = pdf_path.read_bytes()
    text = extract_full_text(pdf_bytes)
    txs = extract_bradesco_mensal(pdf_bytes)
    deduped = dedupe_transactions(txs)
    rules = get_bank_rules(BankCode.BRADESCO)

    r_raw = validate_saldo(text, txs, rules)
    r_dedup = validate_saldo(text, deduped, rules)

    print(f"Extraídos: {len(txs)} | Após dedupe: {len(deduped)} | Removidos: {len(txs) - len(deduped)}")
    print(f"Saldo sem dedupe: {r_raw.saldo_calculado} ok={r_raw.ok}")
    print(f"Saldo com dedupe: {r_dedup.saldo_calculado} ok={r_dedup.ok} delta={r_dedup.delta}")

    seen: set[str] = set()
    removed = []
    for tx in txs:
        key = (
            f"{tx.date.isoformat()}|{tx.description.strip()[:80]}|"
            f"{tx.amount:.2f}|{tx.nature.value}"
        )
        if key in seen:
            removed.append(tx)
        else:
            seen.add(key)

    cred_r = sum(t.amount for t in removed if t.nature.value == "credito")
    deb_r = sum(t.amount for t in removed if t.nature.value == "debito")
    print(f"Removidos pelo dedupe: crédito R$ {cred_r:,.2f} | débito R$ {deb_r:,.2f}")
    print(f"Impacto no saldo (créd - déb): R$ {cred_r - deb_r:,.2f}")

    print("\nExemplos removidos (duplicatas legítimas):")
    for tx in removed[:15]:
        print(f"  {tx.date} | {tx.nature.value:6} | R$ {tx.amount:>10,.2f} | {tx.description[:55]}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
