# rotas/alugueis.py — o recurso /alugueis

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dependencias import OPERACAO, operador_logado, pega_sessao
from eventos import registra_evento
from modelos import Aluguel, Atendente
from recibos import DadosRecibo, envia_recibo
from schemas import AluguelEntrada, AluguelSaida, Devolucao
from servicos import finaliza_aluguel, registra_aluguel

router = APIRouter(tags=["aluguéis"])


@router.get("/alugueis", response_model=list[AluguelSaida], dependencies=OPERACAO)
def lista_alugueis(ativos: bool = False, sessao: Session = Depends(pega_sessao)):
    consulta = (
        select(Aluguel)
        .options(selectinload(Aluguel.cliente), selectinload(Aluguel.veiculo))
        .order_by(Aluguel.id)
    )
    if ativos:
        consulta = consulta.where(Aluguel.finalizado == False)
    return sessao.scalars(consulta).all()


@router.post("/alugueis", response_model=AluguelSaida, status_code=status.HTTP_201_CREATED)
def cria_aluguel(
    dados: AluguelEntrada,
    tarefas: BackgroundTasks,
    atendente: Atendente = Depends(operador_logado),
    sessao: Session = Depends(pega_sessao),
):
    registra_evento(
        sessao, atendente, "aluguel.registrado", f"{dados.cpf} {dados.placa} {dados.dias} dias"
    )
    aluguel = registra_aluguel(sessao, dados.cpf, dados.placa, dados.dias, dados.inicio)
    recibo = DadosRecibo(
        numero=aluguel.id,
        cliente=aluguel.cliente.nome,
        placa=aluguel.veiculo.placa,
        modelo=aluguel.veiculo.modelo,
        dias=aluguel.dias,
        inicio=aluguel.inicio,
        valor=aluguel.valor_final,
    )
    tarefas.add_task(envia_recibo, recibo)
    return aluguel


@router.post("/alugueis/{aluguel_id}/finalizar", response_model=AluguelSaida)
def finaliza(
    aluguel_id: int,
    dados: Devolucao | None = None,
    atendente: Atendente = Depends(operador_logado),
    sessao: Session = Depends(pega_sessao),
):
    data = dados.data if dados is not None else None
    registra_evento(sessao, atendente, "aluguel.finalizado", f"#{aluguel_id}")
    return finaliza_aluguel(sessao, aluguel_id, data)
