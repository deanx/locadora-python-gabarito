# rentabilidade.py — faturamento por mês e classificação da frota

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modelos import Aluguel, Veiculo


@dataclass(frozen=True)
class DesempenhoVeiculo:
    placa: str
    alugueis: int
    faturamento: Decimal

    @property
    def classificacao(self) -> str:
        match self:
            case DesempenhoVeiculo(alugueis=0):
                return "parado"
            case DesempenhoVeiculo(faturamento=f) if f >= Decimal("1000"):
                return "estrela"
            case _:
                return "regular"


def faturamento_por_mes(sessao: Session) -> dict[str, Decimal]:
    por_mes: defaultdict[str, Decimal] = defaultdict(Decimal)
    for aluguel in sessao.scalars(select(Aluguel)):
        por_mes[aluguel.inicio.strftime("%Y-%m")] += aluguel.valor_final + aluguel.multa
    return dict(sorted(por_mes.items()))


def desempenho_da_frota(sessao: Session) -> list[DesempenhoVeiculo]:
    """Uma consulta só: o banco agrupa e soma (o LEFT JOIN mantém os veículos parados)."""
    faturamento = func.coalesce(func.sum(Aluguel.valor_final + Aluguel.multa), 0)
    consulta = (
        select(Veiculo.placa, func.count(Aluguel.id), faturamento)
        .outerjoin(Aluguel, Aluguel.veiculo_id == Veiculo.id)
        .group_by(Veiculo.id, Veiculo.placa)
        .order_by(faturamento.desc(), Veiculo.placa)
    )
    return [
        DesempenhoVeiculo(placa, vezes, Decimal(str(total)))
        for placa, vezes, total in sessao.execute(consulta)
    ]
