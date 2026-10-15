# tests/conftest.py — preparação comum a todos os testes

import os
import tempfile

# Os testes usam um banco separado — nunca o banco de verdade.
# Esta linha precisa vir ANTES de importar qualquer coisa do sistema.
# Por padrão, um SQLite descartável; o CI (Aula 70) aponta para um PostgreSQL de teste.
os.environ["LOCADORA_URL_BANCO"] = os.getenv(
    "LOCADORA_URL_BANCO_TESTE", "sqlite:///teste_locadora.db"
)

os.environ.setdefault("LOCADORA_PASTA_RECIBOS", tempfile.mkdtemp(prefix="recibos-"))

import pytest
from fastapi.testclient import TestClient

from api import app
from banco import Base, SessaoLocal, engine
from modelos import Atendente, Cliente, Veiculo
from seguranca import gera_hash


@pytest.fixture
def cliente_http():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessaoLocal() as sessao:
        sessao.add_all(
            [
                Veiculo(
                    placa="ABC1D23",
                    tipo="Carro",
                    modelo="Chevrolet Onix",
                    ano=2023,
                    diaria=120.50,
                    portas=4,
                ),
                Veiculo(
                    placa="MNO3P45",
                    tipo="Moto",
                    modelo="Honda CG 160",
                    ano=2023,
                    diaria=60.00,
                    cilindrada=160,
                ),
                Cliente(nome="Ana Silva", cpf="12345678909", idade=32, plano="Prata"),
                Cliente(nome="Carla Mendes", cpf="11122233344", idade=16),
                Atendente(
                    usuario="balcao",
                    nome="Atendente de Teste",
                    senha_hash=gera_hash("senha-de-teste"),
                ),
                Atendente(
                    usuario="chefe",
                    nome="Gerente de Teste",
                    senha_hash=gera_hash("senha-do-chefe"),
                    papel="gerente",
                ),
                Atendente(
                    usuario="fiscal",
                    nome="Auditor de Teste",
                    senha_hash=gera_hash("senha-do-fiscal"),
                    papel="auditor",
                ),
            ]
        )
        sessao.commit()
    return TestClient(app)


@pytest.fixture
def cliente_logado(cliente_http):
    resposta = cliente_http.post(
        "/login", data={"username": "balcao", "password": "senha-de-teste"}
    )
    token = resposta.json()["access_token"]
    cliente_http.headers["Authorization"] = f"Bearer {token}"
    return cliente_http


@pytest.fixture
def cliente_gerente(cliente_http):
    resposta = cliente_http.post("/login", data={"username": "chefe", "password": "senha-do-chefe"})
    token = resposta.json()["access_token"]
    cliente_http.headers["Authorization"] = f"Bearer {token}"
    return cliente_http


@pytest.fixture
def cliente_auditor(cliente_http):
    resposta = cliente_http.post(
        "/login", data={"username": "fiscal", "password": "senha-do-fiscal"}
    )
    token = resposta.json()["access_token"]
    cliente_http.headers["Authorization"] = f"Bearer {token}"
    return cliente_http
