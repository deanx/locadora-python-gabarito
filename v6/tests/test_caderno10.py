# tests/test_caderno10.py — o endereço preenchido pelo CEP no cadastro

import httpx
import pytest
import respx

import enderecos

URL_SE = f"{enderecos.URL_SERVICO_CEP}/01001000/json/"
PRACA_DA_SE = {
    "cep": "01001-000",
    "logradouro": "Praça da Sé",
    "bairro": "Sé",
    "localidade": "São Paulo",
    "uf": "SP",
}
DIEGO = {"nome": "Diego Rocha", "cpf": "555.666.777-20", "idade": 30}


@pytest.fixture
def servico_cep():
    """Simula o serviço de CEP durante um teste que também usa o TestClient."""
    with respx.mock() as simulador:
        yield simulador


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    async def nao_espera(segundos: float) -> None:
        pass

    monkeypatch.setattr(enderecos.asyncio, "sleep", nao_espera)


def test_cadastro_preenche_endereco(servico_cep, cliente_logado):
    servico_cep.get(URL_SE).mock(return_value=httpx.Response(200, json=PRACA_DA_SE))
    resposta = cliente_logado.post("/clientes", json={**DIEGO, "cep": "01001-000"})
    assert resposta.status_code == 201
    assert resposta.json()["cidade"] == "São Paulo"
    assert resposta.json()["uf"] == "SP"


def test_cep_inexistente_recusa_o_cadastro(servico_cep, cliente_logado):
    servico_cep.get(URL_SE).mock(return_value=httpx.Response(200, json={"erro": "true"}))
    resposta = cliente_logado.post("/clientes", json={**DIEGO, "cep": "01001000"})
    assert resposta.status_code == 422


def test_servico_fora_cadastra_sem_endereco(servico_cep, cliente_logado):
    servico_cep.get(URL_SE).mock(side_effect=httpx.ConnectError("caiu"))
    resposta = cliente_logado.post("/clientes", json={**DIEGO, "cep": "01001000"})
    assert resposta.status_code == 201
    assert resposta.json()["cep"] == "01001000"
    assert resposta.json()["cidade"] is None


def test_sem_cep_continua_como_antes(cliente_logado):
    assert cliente_logado.post("/clientes", json=DIEGO).status_code == 201
