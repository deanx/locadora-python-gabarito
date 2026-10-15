# historico.py — o histórico de um cliente

from decimal import Decimal

from sqlalchemy.orm import Session

from moeda import formata_brl
from servicos import busca_cliente


def mostra_historico(sessao: Session, cpf: str) -> None:
    cliente = busca_cliente(sessao, cpf)
    print(f"Histórico de {cliente}")
    if not cliente.alugueis:
        print("  (nenhum aluguel)")
        return
    for aluguel in cliente.alugueis:
        print(" ", aluguel)
    total = sum((a.valor_final for a in cliente.alugueis), Decimal("0"))
    finalizados = sum(1 for a in cliente.alugueis if a.finalizado)
    quantidade = len(cliente.alugueis)
    palavra = "aluguel" if quantidade == 1 else "aluguéis"
    print(f"  Total: {quantidade} {palavra} ({finalizados} finalizados), {formata_brl(total)}")
