from acc_nomad.services.fallback_extractor import extract_all_local
from acc_nomad.services.rule_classifier import classify_with_rules


def test_bradesco_multiline_format():
    text = """
02/01/2025
PIX RECEBIDO
REM: CLIENTE A
500,00 C
02/01/2025 0131467 TRANSFERENCIA PIX
REM: CLIENTE B
300,00 C
03/01/2025
TARIFA PACOTE SERVICOS
29,90 D
SALDO FINAL
11.270,10 C
"""
    txs = extract_all_local(text)
    assert len(txs) == 3
    assert txs[0].amount == 500.0
    assert txs[1].amount == 300.0
    assert txs[2].nature.value == "debito"


def test_saldo_lines_not_extracted():
    text = """
SALDO ANTERIOR
10.000,00 C
02/01/2025
PIX TESTE
100,00 C
"""
    txs = extract_all_local(text)
    assert len(txs) == 1
    assert "SALDO" not in txs[0].description.upper()


def test_rule_classifier_tarifa():
    text = """
03/01/2025
TARIFA PACOTE
29,90 D
"""
    txs = classify_with_rules(extract_all_local(text))
    assert txs[0].category == "Multas / Tarifas"


def test_mercado_pago_inline():
    text = """
02/01/2025 Pagamento recebido cliente X R$ 220,00
03/01/2025 Compra cartão loja Y -R$ 50,00
"""
    txs = extract_all_local(text)
    assert len(txs) >= 2
    assert any(t.nature.value == "credito" for t in txs)
    assert any(t.nature.value == "debito" for t in txs)
