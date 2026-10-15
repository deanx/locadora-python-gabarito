# rotas/autenticacao.py — o login e a identificação do atendente

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from dependencias import atendente_logado, pega_sessao
from modelos import Atendente
from schemas import AtendenteSaida, Token
from seguranca import confere_senha, cria_token, gera_hash

router = APIRouter(tags=["autenticação"])

HASH_FALSO = gera_hash(secrets.token_urlsafe(16))


@router.post("/login", response_model=Token)
def login(
    formulario: OAuth2PasswordRequestForm = Depends(), sessao: Session = Depends(pega_sessao)
):
    atendente = sessao.scalar(select(Atendente).where(Atendente.usuario == formulario.username))
    usuario, senha_hash = (atendente.usuario, atendente.senha_hash) if atendente else ("", "")
    sessao.rollback()  # devolve a conexão ao grupo ANTES do cálculo lento da senha
    # Sem usuário, confere contra um hash falso: o tempo da resposta não pode revelar quem existe
    senha_certa = confere_senha(formulario.password, senha_hash or HASH_FALSO)
    if not senha_hash or not senha_certa:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": cria_token(usuario), "token_type": "bearer"}


@router.get("/eu", response_model=AtendenteSaida)
def eu(atendente: Atendente = Depends(atendente_logado)):
    return atendente
