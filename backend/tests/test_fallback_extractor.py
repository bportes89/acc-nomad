from acc_nomad.services.fallback_extractor import extract_all_local


def test_extract_bradesco_cd_format():
    text = """
02/01/2025
PIX RECEBIDO JOAO SILVA
1.234,56 C
03/01/2025
TARIFA BANCARIA
12,00 D
"""
    txs = extract_all_local(text)
    assert len(txs) == 2
    assert txs[0].amount == 1234.56
    assert txs[1].nature.value == "debito"


def test_extract_sicoob_rs_format():
    text = """
02/01/2025
14:46:35
Recebimento Pix via chave
CLAUDIO MANOEL CAMARGO JUNIOR
BCO BRADESCO S.A.
R$ 220,00
03/01/2025
16:02:51
Recebimento Pix copia e cola
Carlos Cesar do Nascimento Santos
R$ 423,13
"""
    txs = extract_all_local(text)
    assert len(txs) == 2
    assert txs[0].amount == 220.0
    assert txs[1].amount == 423.13
