# rotas/veiculos.py — o recurso /veiculos

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dependencias import gerente_logado, pega_sessao
from eventos import registra_evento
from modelos import Atendente, Veiculo
from periodo import Periodo
from schemas import Disponibilidade, Pagina, VeiculoAtualizacao, VeiculoEntrada, VeiculoSaida
from servicos import OperacaoInvalida, busca_veiculo

router = APIRouter(tags=["veículos"])


@router.get("/veiculos", response_model=list[VeiculoSaida])
def lista_veiculos(
    tipo: str | None = None, disponivel: bool | None = None, sessao: Session = Depends(pega_sessao)
):
    consulta = select(Veiculo).order_by(Veiculo.placa)
    if tipo is not None:
        consulta = consulta.where(Veiculo.tipo == tipo)
    if disponivel is not None:
        consulta = consulta.where(Veiculo.disponivel == disponivel)
    return sessao.scalars(consulta).all()


@router.get("/veiculos/{placa}", response_model=VeiculoSaida)
def detalha_veiculo(placa: str, sessao: Session = Depends(pega_sessao)):
    return busca_veiculo(sessao, placa)


@router.post("/veiculos", response_model=VeiculoSaida, status_code=status.HTTP_201_CREATED)
def cadastra_veiculo(
    dados: VeiculoEntrada,
    gerente: Atendente = Depends(gerente_logado),
    sessao: Session = Depends(pega_sessao),
):
    existe = sessao.scalar(select(Veiculo).where(Veiculo.placa == dados.placa))
    if existe is not None:
        raise OperacaoInvalida(f"Já existe um veículo com a placa {dados.placa}")
    veiculo = Veiculo(**dados.model_dump())
    sessao.add(veiculo)
    registra_evento(sessao, gerente, "veiculo.cadastrado", f"{veiculo.placa} {veiculo.modelo}")
    sessao.commit()
    return veiculo


@router.patch("/veiculos/{placa}", response_model=VeiculoSaida)
def atualiza_veiculo(
    placa: str,
    dados: VeiculoAtualizacao,
    gerente: Atendente = Depends(gerente_logado),
    sessao: Session = Depends(pega_sessao),
):
    veiculo = busca_veiculo(sessao, placa)
    mudancas = dados.model_dump(exclude_none=True)
    for campo, valor in mudancas.items():
        setattr(veiculo, campo, valor)
    registra_evento(sessao, gerente, "veiculo.alterado", f"{veiculo.placa} {mudancas}")
    sessao.commit()
    return veiculo


@router.delete("/veiculos/{placa}", status_code=status.HTTP_204_NO_CONTENT)
def remove_veiculo(
    placa: str,
    gerente: Atendente = Depends(gerente_logado),
    sessao: Session = Depends(pega_sessao),
) -> None:
    veiculo = busca_veiculo(sessao, placa)
    if veiculo.alugueis:
        raise OperacaoInvalida(
            f"Veículo {veiculo.placa} tem aluguéis registrados e não pode ser removido"
        )
    sessao.delete(veiculo)
    registra_evento(sessao, gerente, "veiculo.removido", veiculo.placa)
    sessao.commit()


@router.get("/veiculos-paginados", response_model=Pagina[VeiculoSaida])
def lista_veiculos_paginados(
    pagina: int = Query(default=1, ge=1),
    tamanho: int = Query(default=20, ge=1, le=100),
    sessao: Session = Depends(pega_sessao),
) -> Pagina[VeiculoSaida]:
    total = sessao.scalar(select(func.count(Veiculo.id))) or 0
    consulta = select(Veiculo).order_by(Veiculo.placa).limit(tamanho).offset((pagina - 1) * tamanho)
    itens = [VeiculoSaida.model_validate(v) for v in sessao.scalars(consulta)]
    return Pagina[VeiculoSaida](itens=itens, pagina=pagina, tamanho=tamanho, total=total)


@router.get("/veiculos/{placa}/disponibilidade", response_model=Disponibilidade)
def disponibilidade(
    placa: str, inicio: date, fim: date, sessao: Session = Depends(pega_sessao)
) -> Disponibilidade:
    veiculo = busca_veiculo(sessao, placa)
    try:
        pedido = Periodo(inicio, fim)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    conflitos = [
        a.id
        for a in veiculo.alugueis
        if not a.finalizado and (Periodo(a.inicio, a.devolucao_prevista) & pedido) is not None
    ]
    return Disponibilidade(
        placa=veiculo.placa, inicio=inicio, fim=fim, livre=not conflitos, conflitos=conflitos
    )
