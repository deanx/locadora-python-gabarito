# tests/test_seguranca_api.py — os achados da auditoria da Aula 95, como testes

from datetime import UTC, datetime, timedelta

import jwt

from rotas import autenticacao


def test_token_assinado_com_a_antiga_chave_padrao_e_recusado(cliente_http):
    validade = datetime.now(UTC) + timedelta(hours=1)
    forjado = jwt.encode(
        {"sub": "chefe", "exp": validade}, "chave-de-desenvolvimento-troque-em-producao", "HS256"
    )
    resposta = cliente_http.get("/eu", headers={"Authorization": f"Bearer {forjado}"})
    assert resposta.status_code == 401


def test_token_sem_assinatura_e_recusado(cliente_http):
    validade = datetime.now(UTC) + timedelta(hours=1)
    sem_assinatura = jwt.encode({"sub": "chefe", "exp": validade}, None, algorithm="none")
    resposta = cliente_http.get("/eu", headers={"Authorization": f"Bearer {sem_assinatura}"})
    assert resposta.status_code == 401


def test_usuario_inexistente_tambem_confere_senha(cliente_http, monkeypatch):
    chamadas: list[str] = []
    original = autenticacao.confere_senha

    def espia(senha: str, senha_hash: str) -> bool:
        chamadas.append(senha_hash)
        return original(senha, senha_hash)

    monkeypatch.setattr("rotas.autenticacao.confere_senha", espia)
    resposta = cliente_http.post("/login", data={"username": "fantasma", "password": "x"})
    assert resposta.status_code == 401
    assert chamadas == [autenticacao.HASH_FALSO]
