# test_caderno14.py — a busca sem acento e o nome normalizado (caderno do Módulo 14)

import unicodedata

from texto import chave_busca, normaliza_nome

JOSE = {"nome": "José Araújo", "cpf": "52998224725", "idade": 40}


def test_chave_busca_ignora_acentos_e_maiusculas():
    assert chave_busca("JOÃO Conceição") == "joao conceicao"


def test_normaliza_nome_junta_acentos_e_limpa_espacos():
    separado = unicodedata.normalize("NFD", "  José   Araújo ")
    assert normaliza_nome(separado) == "José Araújo"
    assert len(normaliza_nome(separado)) == len("José Araújo")


def test_busca_sem_acento(cliente_logado):
    assert cliente_logado.post("/clientes", json=JOSE).status_code == 201
    for termo in ["jose", "JOSÉ", "araujo", "sé ar"]:
        resposta = cliente_logado.get("/clientes", params={"busca": termo})
        assert [c["nome"] for c in resposta.json()] == ["José Araújo"], termo


def test_busca_sem_resultado(cliente_logado):
    resposta = cliente_logado.get("/clientes", params={"busca": "ninguém"})
    assert resposta.json() == []


def test_nome_separado_vira_junto_no_cadastro(cliente_logado):
    separado = dict(JOSE, nome=unicodedata.normalize("NFD", "José Araújo"))
    assert cliente_logado.post("/clientes", json=separado).status_code == 201
    resposta = cliente_logado.get("/clientes", params={"busca": "jose"})
    assert resposta.json()[0]["nome"] == "José Araújo"


def test_sem_busca_lista_todos(cliente_logado):
    antes = len(cliente_logado.get("/clientes").json())
    cliente_logado.post("/clientes", json=JOSE)
    assert len(cliente_logado.get("/clientes").json()) == antes + 1


def test_versao_no_openapi_e_na_saude(cliente_http):
    from versao import versao_do_projeto

    esperada = versao_do_projeto()
    assert esperada != "desconhecida"
    assert cliente_http.get("/openapi.json").json()["info"]["version"] == esperada
    assert cliente_http.get("/saude").json()["versao"] == esperada


def test_versao_sem_pyproject_nao_derruba(tmp_path, caplog):
    from versao import versao_do_projeto

    assert versao_do_projeto(tmp_path / "nao_existe.toml") == "desconhecida"
    assert "não encontrei a versão" in caplog.text
