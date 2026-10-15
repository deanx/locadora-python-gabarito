# test_caderno15.py — a conferência de endereços em lote (caderno do Módulo 15)

import asyncio

import httpx
import pytest
import respx

import confere_enderecos
import enderecos
from confere_enderecos import confere_ceps
from enderecos import Endereco

# A fixture sem_espera troca o asyncio.sleep do Python INTEIRO durante o teste
# (enderecos.asyncio é o próprio módulo asyncio). Aqui fica guardado o verdadeiro.
SLEEP_DE_VERDADE = asyncio.sleep


def url(cep: str) -> str:
    return f"{enderecos.URL_SERVICO_CEP}/{cep}/json/"


def resposta(cidade: str) -> dict:
    return {"logradouro": "Rua A", "bairro": "Centro", "localidade": cidade, "uf": "SP"}


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    async def nao_espera(segundos: float) -> None:
        pass

    monkeypatch.setattr(enderecos.asyncio, "sleep", nao_espera)


@respx.mock
def test_confere_todos():
    respx.get(url("01001000")).mock(return_value=httpx.Response(200, json=resposta("São Paulo")))
    respx.get(url("13010000")).mock(return_value=httpx.Response(200, json=resposta("Campinas")))
    resultado = asyncio.run(confere_ceps(["01001000", "13010000", "01001000"]))
    assert {cep: e.cidade for cep, e in resultado.encontrados.items()} == {
        "01001000": "São Paulo",
        "13010000": "Campinas",
    }
    assert resultado.falhas == {}


@respx.mock
def test_falhas_esperadas_nao_cancelam_as_outras():
    respx.get(url("01001000")).mock(return_value=httpx.Response(200, json=resposta("São Paulo")))
    respx.get(url("99999999")).mock(return_value=httpx.Response(200, json={"erro": "true"}))
    respx.get(url("13010000")).mock(return_value=httpx.Response(503))
    resultado = asyncio.run(confere_ceps(["01001000", "99999999", "13010000"]))
    assert list(resultado.encontrados) == ["01001000"]
    assert resultado.falhas == {
        "99999999": "CepNaoEncontrado",
        "13010000": "ServicoCepIndisponivel",
    }


def test_nunca_passa_do_limite(monkeypatch):
    ativas = pico = 0

    async def falsa(cep: str) -> Endereco:
        nonlocal ativas, pico
        ativas += 1
        pico = max(pico, ativas)
        await SLEEP_DE_VERDADE(0.01)
        ativas -= 1
        return Endereco(cep=cep, logradouro="Rua A", bairro="Centro", cidade="X", uf="SP")

    monkeypatch.setattr(confere_enderecos.enderecos, "busca_endereco", falsa)
    resultado = asyncio.run(confere_ceps([f"{n:08d}" for n in range(40)], limite_simultaneo=5))
    assert len(resultado.encontrados) == 40
    assert pico == 5


def test_erro_inesperado_cancela_o_lote(monkeypatch):
    async def quebrada(cep: str) -> Endereco:
        raise RuntimeError("bug no código, e não falha do serviço")

    monkeypatch.setattr(confere_enderecos.enderecos, "busca_endereco", quebrada)
    with pytest.raises(ExceptionGroup) as erro:
        asyncio.run(confere_ceps(["01001000", "13010000"]))
    assert erro.group_contains(RuntimeError)


def test_divergencias():
    from confere_enderecos import Conferencia, divergencias
    from modelos import Cliente

    ana = Cliente(
        nome="Ana Silva",
        cpf="12345678909",
        idade=32,
        cep="01001000",
        logradouro="Rua A",
        cidade="São Paulo",
        uf="SP",
    )
    bia = Cliente(
        nome="Bia Lima",
        cpf="52998224725",
        idade=28,
        cep="13010000",
        logradouro="Rua A",
        cidade="Santos",
        uf="SP",
    )
    caio = Cliente(nome="Caio Reis", cpf="11144477735", idade=40, cep="99999999")
    sem_cep = Cliente(nome="Duda Costa", cpf="39053344705", idade=22)
    conferencia = Conferencia(
        encontrados={
            "01001000": Endereco(
                cep="01001000", logradouro="Rua A", bairro="Centro", cidade="São Paulo", uf="SP"
            ),
            "13010000": Endereco(
                cep="13010000", logradouro="Rua A", bairro="Centro", cidade="Campinas", uf="SP"
            ),
        },
        falhas={"99999999": "CepNaoEncontrado"},
    )
    assert divergencias([ana, bia, caio, sem_cep], conferencia) == [
        "Bia Lima: cadastro diz Santos/SP, o CEP diz Campinas/SP",
        "Caio Reis: não conferido (CepNaoEncontrado)",
    ]


def test_brl_antigo_ainda_funciona_e_avisa():
    from decimal import Decimal

    from moeda import brl, formata_brl

    with pytest.warns(DeprecationWarning, match="use formata_brl"):
        assert brl(Decimal("1234.5")) == formata_brl(Decimal("1234.5")) == "R$ 1.234,50"
