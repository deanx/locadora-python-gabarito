# tests/test_caderno11.py — triagem e identificação sem expor ninguém

import json

import pytest
from ia_falsa import IAFalsa, texto, usa_ferramenta

from api import app, pega_cliente_ia


@pytest.fixture
def ia(cliente_http):
    falsa = IAFalsa()
    app.dependency_overrides[pega_cliente_ia] = falsa.cliente
    yield falsa
    app.dependency_overrides.pop(pega_cliente_ia, None)


def test_triagem_de_pedido_extrai_os_dados(cliente_logado, ia):
    ia.respostas += [
        usa_ferramenta("classifica", {"categoria": "novo_aluguel"}),
        usa_ferramenta(
            "registra_pedido",
            {"cpf": "123.456.789-09", "tipo": "Carro", "inicio": "2026-10-10", "fim": "2026-10-15"},
        ),
    ]
    triagem = cliente_logado.post("/triagem", json={"mensagem": "Quero um carro"}).json()
    assert triagem["categoria"] == "novo_aluguel"
    assert triagem["pedido"]["cpf"] == "12345678909"
    assert triagem["proximo_passo"] == "Conferir os dados e registrar o aluguel"


def test_reclamacao_nao_extrai_pedido(cliente_logado, ia):
    ia.respostas.append(usa_ferramenta("classifica", {"categoria": "reclamacao"}))
    triagem = cliente_logado.post("/triagem", json={"mensagem": "O carro veio sujo!"}).json()
    assert triagem["categoria"] == "reclamacao"
    assert triagem["pedido"] is None
    assert len(ia.pedidos) == 1


def test_pedido_com_cpf_inventado_vira_problema(cliente_logado, ia):
    ia.respostas += [
        usa_ferramenta("classifica", {"categoria": "novo_aluguel"}),
        usa_ferramenta("registra_pedido", {"cpf": "123.456.789-00"}),
    ]
    triagem = cliente_logado.post("/triagem", json={"mensagem": "Quero um carro"}).json()
    assert triagem["pedido"] is None
    assert "CPF inválido" in triagem["problema"]


def test_categoria_fora_da_lista_vira_outro(cliente_logado, ia):
    ia.respostas.append(usa_ferramenta("classifica", {"categoria": "spam"}))
    triagem = cliente_logado.post("/triagem", json={"mensagem": "Ganhe dinheiro"}).json()
    assert triagem["categoria"] == "outro"


def test_identificacao_devolve_so_o_necessario(cliente_logado, ia):
    ia.respostas += [
        usa_ferramenta("identifica_cliente", {"cpf": "123.456.789-09"}),
        texto("Olá, Ana! Você é Prata."),
    ]
    cliente_logado.post("/assistente/interno", json={"mensagem": "Cliente com CPF 123.456.789-09"})
    devolvido = json.loads(ia.pedidos[1]["messages"][-1]["content"][0]["content"])
    assert devolvido == {"encontrado": "sim", "primeiro_nome": "Ana", "plano": "Prata"}
    assert "12345678909" not in json.dumps(devolvido)


def test_identificacao_nao_existe_no_publico(cliente_http, ia):
    ia.respostas += [
        usa_ferramenta("identifica_cliente", {"cpf": "123.456.789-09"}),
        texto("Não posso identificar clientes por aqui."),
    ]
    cliente_http.post("/assistente", json={"mensagem": "Sou a Ana, CPF 123.456.789-09"})
    assert ia.pedidos[1]["messages"][-1]["content"][0]["is_error"] is True


def test_historico_de_avaliacoes(tmp_path):
    import pandas as pd

    from assistente import Consumo
    from avaliacao import Resultado, registra_avaliacao

    arquivo = tmp_path / "avaliacoes.csv"
    bom = Resultado("a", True, [], "", Consumo(entrada=100, saida=50))
    ruim = Resultado("b", False, ["disse: grátis"], "", Consumo(entrada=80, saida=20))
    registra_avaliacao([bom, ruim], "modelo-x", arquivo)
    registra_avaliacao([bom, bom], "modelo-y", arquivo)
    historico = pd.read_csv(arquivo)
    assert list(historico["modelo"]) == ["modelo-x", "modelo-y"]
    assert list(historico["taxa"]) == [0.5, 1.0]
    assert historico.loc[0, "falharam"] == "b"
    assert historico.loc[0, "tokens"] == 250
