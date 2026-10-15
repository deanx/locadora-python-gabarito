# Locadora Python — gabarito

![CI](https://github.com/deanx/locadora-python-gabarito/actions/workflows/ci.yml/badge.svg)

Sistema de uma locadora de veículos, desenvolvido em Python ao longo do
curso **Python do zero ao profissional**. Este repositório é o
**gabarito**: o estado do sistema no fim do curso, para você comparar com
o seu.

Começa como um programa de terminal e termina como uma API web com banco
de dados, autenticação, testes automáticos, contêiner e integração
contínua.

## Recursos

- API REST com FastAPI: veículos, clientes e aluguéis (documentação
  interativa em `/docs`)
- Login com JWT e senhas guardadas com Argon2; papéis de atendente e
  gerente
- Banco PostgreSQL (ou SQLite, no desenvolvimento), com 11 migrações
  do Alembic
- Cálculo de diárias com descontos por prazo e planos de fidelidade
- Consulta de endereço pelo CEP (ViaCEP), com prazo e novas tentativas
- Relatórios para a gerência em Excel e gráficos
- Assistente de atendimento com um modelo de linguagem (Anthropic), com
  ferramentas e permissões
- 133 testes automáticos, que rodam no SQLite e no PostgreSQL

## Instalação

Requer Python 3.15 e o [uv](https://docs.astral.sh/uv/).

    git clone https://github.com/deanx/locadora-python-gabarito.git
    cd locadora-python-gabarito
    uv sync

## Uso

O jeito mais simples é com o Docker, que sobe a API e o PostgreSQL juntos:

    docker compose up --build

Sem o Docker, com o SQLite:

    cd v6
    uv run alembic upgrade head
    uv run python cria_atendente.py
    uv run uvicorn api:app --reload

Depois, abra http://127.0.0.1:8000/docs no navegador.

Para rodar os testes:

    cd v6
    uv run python -m pytest

## Tecnologias

- Python 3.15
- FastAPI, Pydantic e Uvicorn
- SQLAlchemy, Alembic e PostgreSQL
- PyJWT e pwdlib (Argon2)
- httpx, pandas, matplotlib e openpyxl
- SDK da Anthropic
- pytest, ruff, mypy, Docker e GitHub Actions

## Licença

MIT — veja o arquivo `LICENSE`.
