# tests/test_assistente.py — o ciclo de ferramentas, com o modelo de mentira e o banco de verdade

import json

import pytest
from ia_falsa import IAFalsa, mensagem, texto, usa_ferramenta

from assistente import LimiteDeVoltas, responde
from banco import SessaoLocal


def resultado_enviado(pedido: dict, indice: int = 0) -> dict:
    """O bloco tool_result que o sistema mandou de volta ao modelo."""
    return pedido["messages"][-1]["content"][indice]


def test_consulta_a_frota_de_verdade(cliente_http):
    falsa = IAFalsa(
        usa_ferramenta("consulta_frota", {"tipo": "Moto"}),
        texto("Temos a Honda CG 160, por R$ 60,00 a diária."),
    )
    historico = [{"role": "user", "content": "Vocês têm moto?"}]
    with SessaoLocal() as sessao:
        final = responde(falsa.cliente(), sessao, historico)
    assert final == "Temos a Honda CG 160, por R$ 60,00 a diária."
    devolvido = resultado_enviado(falsa.pedidos[1])
    assert devolvido["tool_use_id"] == "toolu_1"
    motos = json.loads(devolvido["content"])
    assert motos == [
        {"placa": "MNO3P45", "modelo": "Honda CG 160", "tipo": "Moto", "diaria": "R$ 60,00"}
    ]


def test_orcamento_usa_o_calculo_do_sistema(cliente_http):
    falsa = IAFalsa(
        usa_ferramenta("calcula_orcamento", {"placa": "ABC1D23", "dias": 5, "cpf": "12345678909"}),
        texto("Para a Ana, 5 dias de Onix saem por R$ 542,25."),
    )
    with SessaoLocal() as sessao:
        responde(falsa.cliente(), sessao, [{"role": "user", "content": "Orçamento"}])
    orcamento = json.loads(resultado_enviado(falsa.pedidos[1])["content"])
    assert orcamento["valor"] == "R$ 542,25"
    assert "Prata" in orcamento["observacao"]


def test_placa_inventada_vira_erro_para_o_modelo(cliente_http):
    falsa = IAFalsa(
        usa_ferramenta("calcula_orcamento", {"placa": "ZZZ9Z99", "dias": 2}),
        texto("Não encontrei esse veículo."),
    )
    with SessaoLocal() as sessao:
        responde(falsa.cliente(), sessao, [{"role": "user", "content": "Quanto o ZZZ?"}])
    devolvido = resultado_enviado(falsa.pedidos[1])
    assert devolvido["is_error"] is True
    assert "ZZZ9Z99" in devolvido["content"]


def test_entrada_fora_do_contrato_vira_erro(cliente_http):
    falsa = IAFalsa(
        usa_ferramenta("calcula_orcamento", {"placa": "ABC1D23", "dias": 400}),
        texto("Só posso orçar até 30 dias."),
    )
    with SessaoLocal() as sessao:
        responde(falsa.cliente(), sessao, [{"role": "user", "content": "400 dias"}])
    assert resultado_enviado(falsa.pedidos[1])["is_error"] is True


def test_o_ciclo_tem_limite(cliente_http):
    falsa = IAFalsa(*[usa_ferramenta("consulta_frota", {}) for _ in range(5)])
    with SessaoLocal() as sessao, pytest.raises(LimiteDeVoltas):
        responde(falsa.cliente(), sessao, [{"role": "user", "content": "Oi"}])
    assert len(falsa.pedidos) == 5


def test_duas_ferramentas_na_mesma_resposta(cliente_http):
    duas = mensagem(
        [
            {
                "type": "tool_use",
                "id": "toolu_a",
                "name": "consulta_frota",
                "input": {"tipo": "Carro"},
            },
            {
                "type": "tool_use",
                "id": "toolu_b",
                "name": "consulta_frota",
                "input": {"tipo": "Moto"},
            },
        ],
        "tool_use",
    )
    falsa = IAFalsa(duas, texto("Temos um carro e uma moto."))
    with SessaoLocal() as sessao:
        responde(falsa.cliente(), sessao, [{"role": "user", "content": "O que tem?"}])
    devolvidos = falsa.pedidos[1]["messages"][-1]["content"]
    assert [d["tool_use_id"] for d in devolvidos] == ["toolu_a", "toolu_b"]
