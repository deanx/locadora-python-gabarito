# seguranca.py — senhas e tokens de acesso

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from config import CHAVE_SECRETA, MINUTOS_TOKEN

ALGORITMO = "HS256"
_hasher = PasswordHash.recommended()


def gera_hash(senha: str) -> str:
    return _hasher.hash(senha)


def confere_senha(senha: str, senha_hash: str) -> bool:
    return _hasher.verify(senha, senha_hash)


def cria_token(usuario: str) -> str:
    validade = datetime.now(UTC) + timedelta(minutes=MINUTOS_TOKEN)
    conteudo = {"sub": usuario, "exp": validade}
    return jwt.encode(conteudo, CHAVE_SECRETA, algorithm=ALGORITMO)


def le_token(token: str) -> str | None:
    """Devolve o usuário dono do token, ou None se o token for inválido ou vencido."""
    try:
        conteudo = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
    except jwt.InvalidTokenError:
        return None
    return conteudo.get("sub")
