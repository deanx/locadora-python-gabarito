# relatorios.py — consultas de gestão da locadora

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modelos import Aluguel, Cliente, Veiculo


@dataclass(frozen=True)
class LinhaFrota:
    tipo: str
    total: int
    disponiveis: int


@dataclass(frozen=True)
class LinhaFaturamento:
    cliente: str
    total: Decimal


@dataclass(frozen=True)
class LinhaMaisAlugado:
    placa: str
    modelo: str
    vezes: int


def frota_por_tipo(sessao: Session) -> list[LinhaFrota]:
    consulta = (
        select(
            Veiculo.tipo,
            func.count(Veiculo.id),
            func.count(Veiculo.id).filter(Veiculo.disponivel == True),
        )
        .group_by(Veiculo.tipo)
        .order_by(Veiculo.tipo)
    )
    return [LinhaFrota(*linha) for linha in sessao.execute(consulta)]


def faturamento_por_cliente(sessao: Session) -> list[LinhaFaturamento]:
    total = func.sum(Aluguel.valor_final).label("total")
    consulta = (
        select(Cliente.nome, total)
        .join(Aluguel, Aluguel.cliente_id == Cliente.id)
        .group_by(Cliente.id)
        .order_by(total.desc())
    )
    return [LinhaFaturamento(*linha) for linha in sessao.execute(consulta)]


def veiculos_mais_alugados(sessao: Session, limite: int = 3) -> list[LinhaMaisAlugado]:
    vezes = func.count(Aluguel.id).label("vezes")
    consulta = (
        select(Veiculo.placa, Veiculo.modelo, vezes)
        .join(Aluguel, Aluguel.veiculo_id == Veiculo.id)
        .group_by(Veiculo.id)
        .order_by(vezes.desc(), Veiculo.placa)
        .limit(limite)
    )
    return [LinhaMaisAlugado(*linha) for linha in sessao.execute(consulta)]


def exporta_frota_csv(sessao: Session, pasta: Path) -> Path:
    """Grava a frota num CSV dentro da pasta, com a data no nome. Devolve o caminho."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"frota-{date.today().isoformat()}.csv"
    campos = ["placa", "tipo", "modelo", "ano", "diaria", "disponivel"]
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for v in sessao.scalars(select(Veiculo).order_by(Veiculo.placa)):
            escritor.writerow({campo: getattr(v, campo) for campo in campos})
    return caminho
