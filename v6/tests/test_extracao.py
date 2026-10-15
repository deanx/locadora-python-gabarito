# tests/test_extracao.py — texto livre virando dados validados

from datetime import date

import pytest
from ia_falsa import IAFalsa, texto, usa_ferramenta

from extracao import ExtracaoInvalida, extrai_pedido

HOJE = date(2026, 10, 6)
MENSAGEM = "Oi, sou a Ana, CPF 123.456.789-09. Quero um carro do dia 10 ao dia 15."


def test_pedido_completo():
    falsa = IAFalsa(
        usa_ferramenta(
            "registra_pedido",
            {
                "nome": "Ana",
                "cpf": "123.456.789-09",
                "tipo": "Carro",
                "inicio": "2026-10-10",
                "fim": "2026-10-15",
                "duvidas": [],
            },
        )
    )
    pedido = extrai_pedido(falsa.cliente(), MENSAGEM, HOJE)
    assert pedido.cpf == "12345678909"
    assert pedido.inicio == date(2026, 10, 10)
    assert pedido.dias == 5


def test_o_pedido_forca_a_ferramenta_e_informa_a_data():
    falsa = IAFalsa(usa_ferramenta("registra_pedido", {"duvidas": ["Qual veículo?"]}))
    extrai_pedido(falsa.cliente(), "Oi", HOJE)
    enviado = falsa.pedidos[0]
    assert enviado["tool_choice"] == {"type": "tool", "name": "registra_pedido"}
    assert "2026-10-06" in enviado["system"]


def test_faltando_dados_vira_duvida():
    falsa = IAFalsa(
        usa_ferramenta("registra_pedido", {"tipo": "Moto", "duvidas": ["Para quais datas?"]})
    )
    pedido = extrai_pedido(falsa.cliente(), "Quero uma moto", HOJE)
    assert pedido.dias is None
    assert pedido.duvidas == ["Para quais datas?"]


@pytest.mark.parametrize(
    "entrada",
    [
        {"cpf": "123.456.789-00"},  # dígito errado: inventado?
        {"inicio": "2026-10-15", "fim": "2026-10-10"},  # datas invertidas
        {"tipo": "Barco"},  # fora do contrato
    ],
)
def test_dados_ruins_do_modelo_sao_barrados(entrada):
    falsa = IAFalsa(usa_ferramenta("registra_pedido", entrada))
    with pytest.raises(ExtracaoInvalida):
        extrai_pedido(falsa.cliente(), MENSAGEM, HOJE)


def test_modelo_que_responde_texto_em_vez_da_ferramenta():
    falsa = IAFalsa(texto("Claro, vou anotar seu pedido!"))
    with pytest.raises(ExtracaoInvalida):
        extrai_pedido(falsa.cliente(), MENSAGEM, HOJE)
