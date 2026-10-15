# tests/test_ia.py — o cliente de IA, testado com o dublê

from ia_falsa import IAFalsa, texto

from ia import pergunta


def test_pergunta_devolve_o_texto_e_manda_o_sistema():
    falsa = IAFalsa(texto("Sim, alugamos motos!"))
    resposta = pergunta(falsa.cliente(), "Você é atendente.", "Vocês alugam moto?")
    assert resposta == "Sim, alugamos motos!"
    assert falsa.pedidos[0]["system"] == "Você é atendente."
    assert falsa.pedidos[0]["messages"] == [{"role": "user", "content": "Vocês alugam moto?"}]
