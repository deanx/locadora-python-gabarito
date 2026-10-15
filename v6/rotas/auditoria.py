# rotas/auditoria.py — o registro de auditoria

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from dependencias import exige_papel, pega_sessao
from modelos import Evento
from papeis import Papel
from schemas import EventoSaida

router = APIRouter(tags=["auditoria"])


@router.get(
    "/auditoria",
    response_model=list[EventoSaida],
    dependencies=[Depends(exige_papel(Papel.GERENTE, Papel.AUDITOR))],
)
def lista_auditoria(
    limite: int = Query(default=50, ge=1, le=500), sessao: Session = Depends(pega_sessao)
):
    consulta = select(Evento).order_by(Evento.id.desc()).limit(limite)
    return sessao.scalars(consulta).all()
