"""Extrator local de lançamentos — Bradesco, Sicoob, Mercado Pago, etc."""

from __future__ import annotations

import re
from datetime import date

from acc_nomad.models import Transaction, TransactionNature

DATE_RE = re.compile(r"\b(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})\b")
DATE_SHORT_RE = re.compile(r"\b(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{2})\b")
DATE_LINE_RE = re.compile(r"^(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{2,4})\s*(.*)$")
AMOUNT_LINE_RE = re.compile(
    r"^(\d{1,3}(?:\.\d{3})*,\d{2})\s*([CD])\s*$",
    re.IGNORECASE,
)
INLINE_AMOUNT_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*([CD])\b",
    re.IGNORECASE,
)
NEG_AMOUNT_RE = re.compile(r"^-\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*$")
DATE_ONLY_RE = re.compile(r"^(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})$")
DATE_SHORT_ONLY_RE = re.compile(r"^(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{2})$")
AMOUNT_ONLY_RE = re.compile(r"^(\d{1,3}(?:\.\d{3})*,\d{2})$")
DOCTO_LINE_RE = re.compile(r"^\d{4,8}$")
RS_AMOUNT_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
MP_ROW_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\s*R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})\s*$"
)
# Unicredi / Sicredi — linha única: data + histórico + valor C/D [+ saldo]
COOP_ROW_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s*([CD])"
    r"(?:\s+\d{1,3}(?:\.\d{3})*,\d{2}\s*[CD])?\s*$",
    re.IGNORECASE,
)
COOP_SIGNED_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([+-])\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*$",
)
AMOUNT_HINT_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*[CD]?|R\$\s*\d|^\+\s*\d|^\-\s*\d",
    re.IGNORECASE,
)

DEBIT_HINTS = (
    "PAGAMENTO", "PAGTO", "DEBITO", "DÉBITO", "TARIFA", "TAXA", "SAQUE",
    "ENVIO PIX", "COMPRA", "SAÍDA", "SAIDA", "COBRANCA", "COBRANÇA",
)
CREDIT_HINTS = (
    "PIX RECEBIDO", "PIX QR", "LIQUIDACAO", "LIQUIDAÇÃO", "TED-", "TED ",
    "VISA CREDITO", "VISA CRÉDITO", "MASTER CREDITO", "MASTER CRÉDITO",
    "TRANSF CC", "CREDITO", "CRÉDITO", "DEPOSITO", "DEPÓSITO",
)
SALDO_KEYWORDS = (
    "SALDO ANTERIOR", "SALDO ANTER", "SALDO FINAL", "SALDO ATUAL",
    "SALDO DO DIA", "S A L D O",
)
SKIP_KEYWORDS = (
    *SALDO_KEYWORDS,
    "LIMITE ESPECIAL",
    "TAXA ",
    "CUSTO EFETIVO",
    "INFORMAC",
    "OBSERV",
    "SAC ",
    "OUVIDORIA",
)


def extract_fallback(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    transactions: list[Transaction] = []
    seen: set[str] = set()
    lines = [ln.strip() for ln in sample_text.splitlines() if ln.strip()]

    current_date: date | None = None
    description_parts: list[str] = []

    for line in lines:
        parsed_date, date_tail = _parse_date_line(line)
        if parsed_date:
            current_date = parsed_date
            description_parts = [date_tail] if date_tail else []
            continue

        amount_line = AMOUNT_LINE_RE.match(line)
        if amount_line and current_date:
            raw_amount, nature_flag = amount_line.groups()
            desc = " ".join(description_parts).strip()
            if _should_skip(desc, desc.upper() if desc else line.upper()):
                description_parts = []
                continue

            tx = _build_transaction(
                current_date, desc, raw_amount, nature_flag, default_category
            )
            if tx and _remember(tx, seen):
                transactions.append(tx)
            description_parts = []
            continue

        neg = NEG_AMOUNT_RE.match(line)
        if neg and current_date:
            desc = " ".join(description_parts).strip()
            if desc and not _should_skip(desc, desc.upper()):
                tx = _build_transaction(current_date, desc, neg.group(1), "D", default_category)
                if tx and _remember(tx, seen):
                    transactions.append(tx)
            description_parts = []
            continue

        inline = INLINE_AMOUNT_RE.search(line)
        if inline and current_date:
            raw_amount, nature_flag = inline.groups()
            desc = DATE_RE.sub("", line)
            desc = INLINE_AMOUNT_RE.sub("", desc).strip(" -|")
            if desc and not _should_skip(desc, desc.upper()):
                tx = _build_transaction(
                    current_date, desc, raw_amount, nature_flag, default_category
                )
                if tx and _remember(tx, seen):
                    transactions.append(tx)
            continue

        if current_date and not _is_noise_line(line):
            description_parts.append(line)

    return transactions


def extract_all_local(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Extrai lançamentos com regex (Bradesco C/D, Sicoob R$, Mercado Pago, etc.)."""
    seen: set[str] = set()
    merged: list[Transaction] = []

    for extractor in (
        extract_fallback,
        _extract_single_line_rows,
        _extract_rs_table,
        _extract_mercado_pago,
    ):
        for tx in extractor(sample_text, default_category=default_category):
            if _remember(tx, seen):
                merged.append(tx)

    return merged


def filter_transaction_candidate_lines(text: str, *, max_lines: int = 800) -> str:
    """Linhas com data + valor — compacta texto para fallback LLM."""
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) < 8:
            continue
        has_date = DATE_RE.search(line) or DATE_SHORT_RE.search(line)
        if has_date and (AMOUNT_HINT_RE.search(line) or RS_AMOUNT_RE.search(line)):
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def _parse_date_parts(day: str, month: str, year: str) -> date | None:
    try:
        y = int(year)
        if y < 100:
            y += 2000 if y < 70 else 1900
        return date(y, int(month), int(day))
    except ValueError:
        return None


def _extract_single_line_rows(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Cooperativas (Unicredi, Sicredi): data + histórico + valor na mesma linha."""
    transactions: list[Transaction] = []

    for line in sample_text.splitlines():
        line = line.strip()
        if not line:
            continue

        match = COOP_ROW_RE.match(line)
        if match:
            date_str, desc, raw_amount, flag = match.groups()
            parts = date_str.split("/")
            if len(parts) != 3:
                continue
            tx_date = _parse_date_parts(parts[0], parts[1], parts[2])
            if not tx_date:
                continue
            desc = re.sub(r"\s{2,}", " ", desc).strip()
            if _should_skip(desc, desc.upper()):
                continue
            tx = _build_transaction(tx_date, desc, raw_amount, flag, default_category)
            if tx:
                transactions.append(tx)
            continue

        signed = COOP_SIGNED_RE.match(line)
        if signed:
            date_str, desc, sign, raw_amount = signed.groups()
            parts = date_str.split("/")
            if len(parts) != 3:
                continue
            tx_date = _parse_date_parts(parts[0], parts[1], parts[2])
            if not tx_date:
                continue
            flag = "C" if sign == "+" else "D"
            desc = re.sub(r"\s{2,}", " ", desc).strip()
            if _should_skip(desc, desc.upper()):
                continue
            tx = _build_transaction(tx_date, desc, raw_amount, flag, default_category)
            if tx:
                transactions.append(tx)

    return transactions


def _parse_date_line(line: str) -> tuple[date | None, str]:
    match = DATE_LINE_RE.match(line.strip())
    if not match:
        return None, line

    day, month, year, tail = match.groups()
    parsed = _parse_date_parts(day, month, year)
    if parsed is None:
        return None, line
    return parsed, tail.strip()


def _extract_rs_table(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    lines = [ln.strip() for ln in sample_text.splitlines() if ln.strip()]
    transactions: list[Transaction] = []
    current_date: date | None = None

    for index, line in enumerate(lines):
        parsed_date, _ = _parse_date_line(line)
        if parsed_date and DATE_ONLY_RE.match(line):
            current_date = parsed_date
            continue

        amount_match = RS_AMOUNT_RE.search(line)
        if not amount_match or not current_date:
            continue

        raw_amount = amount_match.group(1)
        desc = _description_before_amount(lines, index)
        if not desc or _should_skip(desc, desc.upper()):
            continue

        nature_flag = "D" if any(h in desc.upper() for h in DEBIT_HINTS) else "C"
        tx = _build_transaction(current_date, desc, raw_amount, nature_flag, default_category)
        if tx:
            transactions.append(tx)

    return transactions


def _extract_mercado_pago(
    sample_text: str,
    *,
    default_category: str | None = None,
) -> list[Transaction]:
    """Extrato Mercado Pago / ME — linhas com data + descrição + R$."""
    transactions: list[Transaction] = []
    for line in sample_text.splitlines():
        line = line.strip()
        if not line or "R$" not in line:
            continue

        match = MP_ROW_RE.match(line)
        if match:
            date_str, desc, amount_part = match.groups()
            day, month, year = date_str.split("/")
            try:
                tx_date = date(int(year), int(month), int(day))
            except ValueError:
                continue
            raw = RS_AMOUNT_RE.search(amount_part)
            if not raw:
                continue
            is_debit = amount_part.strip().startswith("-")
            nature_flag = "D" if is_debit else "C"
            tx = _build_transaction(tx_date, desc.strip(), raw.group(1), nature_flag, default_category)
            if tx and not _should_skip(desc, desc.upper()):
                transactions.append(tx)
            continue

        # Formato: 02/01/2025 ... R$ 123,45 (sem C/D)
        date_match = DATE_RE.search(line)
        amount_match = RS_AMOUNT_RE.search(line)
        if date_match and amount_match:
            day, month, year = date_match.groups()
            try:
                tx_date = date(int(year), int(month), int(day))
            except ValueError:
                continue
            desc = line
            desc = DATE_RE.sub("", desc)
            desc = RS_AMOUNT_RE.sub("", desc).strip(" -|")
            if len(desc) < 3 or _should_skip(desc, desc.upper()):
                continue
            is_debit = any(h in desc.upper() for h in DEBIT_HINTS) or " -R$" in line
            nature_flag = "D" if is_debit else "C"
            tx = _build_transaction(tx_date, desc, amount_match.group(1), nature_flag, default_category)
            if tx:
                transactions.append(tx)

    return transactions


def _description_before_amount(lines: list[str], amount_index: int) -> str:
    parts: list[str] = []
    for j in range(amount_index - 1, max(amount_index - 10, -1), -1):
        line = lines[j]
        if DATE_ONLY_RE.match(line) or RS_AMOUNT_RE.search(line):
            break
        if _is_noise_line(line) or line in ("-", "Recebimento", "REAL"):
            continue
        if line.startswith("E") and len(line) > 20:
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}$", line):
            continue
        parts.insert(0, line)
        if len(parts) >= 3:
            break
    return " ".join(parts).strip()[:200]


def _build_transaction(
    tx_date: date,
    description: str,
    raw_amount: str,
    nature_flag: str,
    default_category: str | None = None,
) -> Transaction | None:
    if not description or len(description) < 3:
        return None
    if _should_skip(description, description.upper()):
        return None

    amount = float(raw_amount.replace(".", "").replace(",", "."))
    if amount <= 0:
        return None

    nature = (
        TransactionNature.CREDIT
        if nature_flag.upper() == "C"
        else TransactionNature.DEBIT
    )

    if nature == TransactionNature.CREDIT and default_category:
        category = default_category
    else:
        category = "Não classificado (fallback)"

    return Transaction(
        date=tx_date,
        description=description[:200],
        amount=amount,
        nature=nature,
        category=category,
    )


def _should_skip(description: str, upper: str) -> bool:
    if not description:
        return True
    return any(k in upper for k in SKIP_KEYWORDS)


def _is_noise_line(line: str) -> bool:
    if DATE_RE.fullmatch(line.replace(" ", "")):
        return True
    if line.isdigit():
        return True
    if re.fullmatch(r"\d{3}-\d", line):
        return True
    return False


def _remember(tx: Transaction, seen: set[str]) -> bool:
    key = f"{tx.date.isoformat()}|{tx.description}|{tx.amount}|{tx.nature.value}"
    if key in seen:
        return False
    seen.add(key)
    return True
