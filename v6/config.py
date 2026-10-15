# config.py — configurações lidas do ambiente

import os
import secrets
from pathlib import Path

URL_BANCO = os.getenv("LOCADORA_URL_BANCO", "sqlite:///locadora.db")
NOME_LOCADORA = os.getenv("LOCADORA_NOME", "Locadora Python")

# Segredo usado para assinar os tokens de login. Sem valor padrão no código:
# uma chave escrita aqui estaria no repositório, ao alcance de qualquer um (Aula 95).
AMBIENTE = os.getenv("LOCADORA_AMBIENTE", "desenvolvimento")
CHAVE_SECRETA = os.getenv("LOCADORA_CHAVE_SECRETA") or ""
if not CHAVE_SECRETA:
    if AMBIENTE == "producao":
        raise RuntimeError("Defina LOCADORA_CHAVE_SECRETA: a API não sobe em produção sem ela")
    # Em desenvolvimento, uma chave aleatória a cada execução (refaça o login ao reiniciar)
    CHAVE_SECRETA = secrets.token_urlsafe(32)
MINUTOS_TOKEN = int(os.getenv("LOCADORA_MINUTOS_TOKEN", "60"))

# "json" para produção (uma linha JSON por evento) ou "texto" para ler no terminal.
FORMATO_LOG = os.getenv("LOCADORA_FORMATO_LOG", "texto")
NIVEL_LOG = os.getenv("LOCADORA_NIVEL_LOG", "INFO")

# Serviço de CEP (o ViaCEP; nos estudos e testes, um serviço falso local)
URL_SERVICO_CEP = os.getenv("LOCADORA_URL_SERVICO_CEP", "https://viacep.com.br/ws")

# Onde os recibos são "enviados" (uma pasta, no lugar de um serviço de e-mail)
PASTA_RECIBOS = Path(os.getenv("LOCADORA_PASTA_RECIBOS", "caixa_de_saida"))
# Demora simulada do "envio" do recibo, em segundos (para estudar o segundo plano)
ATRASO_RECIBO = float(os.getenv("LOCADORA_ATRASO_RECIBO", "0"))

# Inteligência artificial (Módulo 11)
CHAVE_IA = os.getenv("ANTHROPIC_API_KEY")
MODELO_IA = os.getenv("LOCADORA_MODELO_IA", "claude-haiku-4-5-20251001")

# Preços da IA em dólares por milhão de tokens (consulte a página de preços do modelo).
# Sem eles, o relatório mostra só os tokens.
PRECO_ENTRADA_IA = os.getenv("LOCADORA_PRECO_ENTRADA_IA")
PRECO_SAIDA_IA = os.getenv("LOCADORA_PRECO_SAIDA_IA")
