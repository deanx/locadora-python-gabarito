# rotas/sistema.py — a raiz e a saúde da API

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import NOME_LOCADORA
from dependencias import pega_sessao
from versao import VERSAO

log = logging.getLogger("locadora")
router = APIRouter(tags=["sistema"])


@router.get("/")
def raiz() -> dict:
    return {"mensagem": f"Bem-vindo à {NOME_LOCADORA}"}


@router.get("/saude")
def saude(sessao: Session = Depends(pega_sessao)) -> JSONResponse:
    try:
        sessao.execute(text("SELECT 1"))
    except Exception:
        log.exception("Saúde: o banco não respondeu")
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "fora do ar"})
    return JSONResponse(content={"status": "ok", "banco": "ok", "versao": VERSAO})
