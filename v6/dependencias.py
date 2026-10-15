# dependencias.py — o que as rotas pedem com Depends: a sessão, o login e as permissões

from collections.abc import Callable, Iterator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from banco import SessaoLocal
from modelos import Atendente
from papeis import Papel
from seguranca import le_token


def pega_sessao() -> Iterator[Session]:
    with SessaoLocal() as sessao:
        yield sessao


esquema_oauth = OAuth2PasswordBearer(tokenUrl="login")


def atendente_logado(
    token: str = Depends(esquema_oauth), sessao: Session = Depends(pega_sessao)
) -> Atendente:
    usuario = le_token(token)
    atendente = None
    if usuario is not None:
        atendente = sessao.scalar(select(Atendente).where(Atendente.usuario == usuario))
    if atendente is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login inválido ou expirado — faça login de novo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return atendente


LOGIN = [Depends(atendente_logado)]


def exige_papel(*permitidos: Papel) -> Callable[..., Atendente]:
    """Fabrica uma dependência que só deixa passar quem tem um dos papéis."""

    def confere(atendente: Atendente = Depends(atendente_logado)) -> Atendente:
        if atendente.papel not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seu papel não permite fazer isto",
            )
        return atendente

    return confere


gerente_logado = exige_papel(Papel.GERENTE)
operador_logado = exige_papel(Papel.ATENDENTE, Papel.GERENTE)
OPERACAO = [Depends(operador_logado)]
