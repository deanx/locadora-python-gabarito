# tests/test_enderecos.py — o CEP testado sem o serviço de verdade

import asyncio

import httpx
import pytest
import respx

import enderecos
from enderecos import (
    CepInvalido,
    CepNaoEncontrado,
    ServicoCepIndisponivel,
    busca_endereco,
)

URL_SE = f"{enderecos.URL_SERVICO_CEP}/01001000/json/"
PRACA_DA_SE = {
    "cep": "01001-000",
    "logradouro": "Praça da Sé",
    "bairro": "Sé",
    "localidade": "São Paulo",
    "uf": "SP",
}


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    """As novas tentativas esperam entre si; nos testes, a espera não espera."""

    async def nao_espera(segundos: float) -> None:
        pass

    monkeypatch.setattr(enderecos.asyncio, "sleep", nao_espera)


@respx.mock
@pytest.mark.parametrize("digitado", ["01001000", "01001-000", " 01001-000 "])
def test_cep_encontrado(digitado):
    respx.get(URL_SE).mock(return_value=httpx.Response(200, json=PRACA_DA_SE))
    endereco = asyncio.run(busca_endereco(digitado))
    assert endereco.cidade == "São Paulo"
    assert endereco.cep == "01001000"


@respx.mock
@pytest.mark.parametrize("marca_de_erro", ["true", True])
def test_cep_inexistente(marca_de_erro):
    respx.get(URL_SE).mock(return_value=httpx.Response(200, json={"erro": marca_de_erro}))
    with pytest.raises(CepNaoEncontrado):
        asyncio.run(busca_endereco("01001000"))


@pytest.mark.parametrize("digitado", ["123", "0100100", "010010000", "abcdefgh", ""])
def test_formato_invalido_nem_chama_o_servico(digitado):
    with respx.mock(assert_all_called=False) as servico:
        rota = servico.get(url__regex=r".*")
        with pytest.raises(CepInvalido):
            asyncio.run(busca_endereco(digitado))
        assert rota.call_count == 0


@respx.mock
def test_recusa_do_servico_nao_e_repetida():
    rota = respx.get(URL_SE).mock(return_value=httpx.Response(400))
    with pytest.raises(CepInvalido):
        asyncio.run(busca_endereco("01001000"))
    assert rota.call_count == 1


@respx.mock
def test_tenta_de_novo_e_consegue():
    rota = respx.get(URL_SE).mock(
        side_effect=[
            httpx.Response(503),
            httpx.ConnectError("caiu"),
            httpx.Response(200, json=PRACA_DA_SE),
        ]
    )
    endereco = asyncio.run(busca_endereco("01001000"))
    assert endereco.logradouro == "Praça da Sé"
    assert rota.call_count == 3


@respx.mock
def test_desiste_depois_de_tres_tentativas():
    rota = respx.get(URL_SE).mock(side_effect=httpx.ReadTimeout("demorou"))
    with pytest.raises(ServicoCepIndisponivel):
        asyncio.run(busca_endereco("01001000"))
    assert rota.call_count == 3


def test_api_responde_503_quando_o_servico_cai(cliente_logado, monkeypatch):
    async def servico_fora(cep: str):
        raise ServicoCepIndisponivel("O serviço de CEP não respondeu")

    monkeypatch.setattr("rotas.enderecos.busca_endereco", servico_fora)
    resposta = cliente_logado.get("/enderecos/01001000")
    assert resposta.status_code == 503
    assert resposta.json() == {"erro": "O serviço de CEP não respondeu"}
