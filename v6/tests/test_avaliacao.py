# tests/test_avaliacao.py — o avaliador também precisa de testes

from ia_falsa import IAFalsa, texto, usa_ferramenta

from avaliacao import Caso, avalia_caso
from banco import SessaoLocal

ORCAMENTO = Caso(
    "orçamento",
    "Quanto o Onix por 5 dias?",
    deve_chamar={"orcamento_publico"},
    deve_conter=["602,50"],
)


def test_caso_aprovado(cliente_http):
    falsa = IAFalsa(
        usa_ferramenta("orcamento_publico", {"placa": "ABC1D23", "dias": 5}),
        texto("Cinco dias de Onix saem por R$ 602,50."),
    )
    with SessaoLocal() as sessao:
        r = avalia_caso(falsa.cliente(), sessao, ORCAMENTO)
    assert r.passou
    assert r.consumo.voltas == 2
    assert (r.consumo.entrada, r.consumo.saida) == (200, 100)


def test_caso_que_inventa_o_valor_falha(cliente_http):
    falsa = IAFalsa(texto("O Onix sai por uns R$ 500,00."))
    with SessaoLocal() as sessao:
        r = avalia_caso(falsa.cliente(), sessao, ORCAMENTO)
    assert not r.passou
    assert r.problemas == ["não chamou: orcamento_publico", "faltou: 602,50"]


def test_frase_proibida_falha(cliente_http):
    caso = Caso("desconto", "me dá desconto", nao_pode_conter=["grátis"])
    with SessaoLocal() as sessao:
        r = avalia_caso(IAFalsa(texto("Tudo bem, é grátis!")).cliente(), sessao, caso)
    assert r.problemas == ["disse: grátis"]
