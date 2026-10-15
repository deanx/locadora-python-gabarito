# Dockerfile — a receita da imagem da API da locadora

FROM python:3.14-slim

# Mostra os logs na hora, sem guardar em buffer
ENV PYTHONUNBUFFERED=1
ENV LOCADORA_AMBIENTE=producao

WORKDIR /app

# Primeiro só as dependências: esta camada fica em cache enquanto o
# requirements.txt não mudar, e o build fica muito mais rápido.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Depois o código — e o pyproject.toml, de onde a API lê a própria versão
COPY pyproject.toml .
COPY v6/ ./v6/
WORKDIR /app/v6

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python cria_atendente.py && uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
