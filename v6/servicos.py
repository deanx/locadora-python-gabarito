# servicos.py — as regras de negócio da locadora

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from auditoria import auditado
from dinheiro import arredonda
from modelos import Aluguel, Cliente, Veiculo
from planos import Plano


class NaoEncontrado(Exception):
    """Algo que foi pedido não existe no banco."""


class OperacaoInvalida(Exception):
    """A operação existe, mas as regras do negócio não permitem."""


def busca_veiculo(sessao: Session, placa: str) -> Veiculo:
    veiculo = sessao.scalar(select(Veiculo).where(Veiculo.placa == placa.upper()))
    if veiculo is None:
        raise NaoEncontrado(f"Veículo {placa} não encontrado")
    return veiculo


def busca_cliente(sessao: Session, cpf: str) -> Cliente:
    cliente = sessao.scalar(select(Cliente).where(Cliente.cpf == cpf))
    if cliente is None:
        raise NaoEncontrado(f"Cliente {cpf} não encontrado")
    return cliente


def calcula_valor_final(cliente: Cliente, veiculo: Veiculo, dias: int) -> Decimal:
    valor = veiculo.calcula_valor(dias)
    if cliente.plano is not None:
        valor = valor * (1 - Plano(cliente.plano).desconto)
    return arredonda(valor)


@auditado
def registra_aluguel(
    sessao: Session, cpf: str, placa: str, dias: int, inicio: date | None = None
) -> Aluguel:
    cliente = busca_cliente(sessao, cpf)
    veiculo = busca_veiculo(sessao, placa)

    if dias < 1:
        raise OperacaoInvalida("O aluguel precisa ter pelo menos 1 dia")
    if not cliente.pode_alugar():
        raise OperacaoInvalida(f"{cliente.nome} não pode alugar (menor de idade)")
    if not veiculo.disponivel:
        raise OperacaoInvalida(f"Veículo {veiculo.placa} já está alugado")

    aluguel = Aluguel(
        cliente=cliente,
        veiculo=veiculo,
        dias=dias,
        valor_final=calcula_valor_final(cliente, veiculo, dias),
        inicio=inicio or date.today(),
    )
    veiculo.disponivel = False
    sessao.add(aluguel)
    sessao.commit()
    return aluguel


PROMOCOES = [(6, Plano.PRATA), (3, Plano.BRONZE)]  # (aluguéis finalizados, plano)
ORDEM_PLANOS = [None, *Plano]  # sem plano, depois Bronze, Prata e Ouro


def plano_merecido(finalizados: int) -> Plano | None:
    for minimo, plano in PROMOCOES:
        if finalizados >= minimo:
            return plano
    return None


def aplica_promocao(cliente: Cliente) -> Plano | None:
    """Sobe o plano do cliente se ele merecer. Devolve o plano novo, ou None."""
    finalizados = sum(1 for a in cliente.alugueis if a.finalizado)
    merecido = plano_merecido(finalizados)
    if ORDEM_PLANOS.index(merecido) > ORDEM_PLANOS.index(cliente.plano):
        cliente.plano = merecido
        return merecido
    return None


ACRESCIMO_MULTA = Decimal("0.20")  # cada dia de atraso custa a diária + 20%


def calcula_multa(aluguel: Aluguel, devolucao: date) -> Decimal:
    atraso = (devolucao - aluguel.devolucao_prevista).days
    if atraso <= 0:
        return Decimal("0.00")
    return arredonda(atraso * aluguel.veiculo.diaria * (1 + ACRESCIMO_MULTA))


@auditado
def finaliza_aluguel(sessao: Session, aluguel_id: int, devolucao: date | None = None) -> Aluguel:
    if devolucao is None:
        devolucao = date.today()
    aluguel = sessao.get(Aluguel, aluguel_id)
    if aluguel is None:
        raise NaoEncontrado(f"Aluguel {aluguel_id} não encontrado")
    if aluguel.finalizado:
        raise OperacaoInvalida(f"Aluguel {aluguel_id} já foi finalizado")
    if devolucao < aluguel.inicio:
        raise OperacaoInvalida("A devolução não pode ser antes do início do aluguel")
    aluguel.devolucao = devolucao
    aluguel.multa = calcula_multa(aluguel, devolucao)
    aluguel.finalizado = True
    aluguel.veiculo.disponivel = True
    aplica_promocao(aluguel.cliente)
    sessao.commit()
    return aluguel
