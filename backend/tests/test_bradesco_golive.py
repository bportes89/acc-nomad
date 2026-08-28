from acc_nomad.services.fallback_extractor import extract_all_local, filter_transaction_candidate_lines
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


def test_unicredi_single_line_with_saldo():
    text = """
01/07/2025  PIX RECEBIDO - JOAO SILVA  123456  500,00 C  10.500,00 C
02/07/2025  TARIFA MANUTENCAO CONTA  29,90 D  10.470,10 D
03/07/26  TED ENVIADA FORNECEDOR  1.200,00 D  9.270,10 D
"""
    txs = extract_all_local(text)
    assert len(txs) == 3
    assert txs[0].amount == 500.0
    assert txs[1].nature.value == "debito"
    assert txs[2].date.year == 2026


def test_filter_transaction_lines():
    text = """
UNICREDI DO BRASIL
Termos e condições...
01/07/2025  PIX RECEBIDO  500,00 C  10.500,00 C
02/07/2025  TARIFA  29,90 D
"""
    compact = filter_transaction_candidate_lines(text)
    assert "PIX RECEBIDO" in compact
    assert "Termos" not in compact
    text = """
02/01/2025 Pagamento recebido cliente X R$ 220,00
03/01/2025 Compra cartão loja Y -R$ 50,00
"""
    txs = extract_all_local(text)
    assert len(txs) >= 2
    assert any(t.nature.value == "credito" for t in txs)
    assert any(t.nature.value == "debito" for t in txs)
