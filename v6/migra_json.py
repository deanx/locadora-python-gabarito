# migra_json.py — copia os dados do estado.json para o banco (rodar uma vez)

import json
from decimal import Decimal

from sqlalchemy import select

from banco import SessaoLocal
from modelos import Aluguel, Cliente, Veiculo
from servicos import calcula_valor_final


def migra(caminho: str) -> None:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    with SessaoLocal() as sessao:
        if sessao.scalar(select(Veiculo)) is not None:
            print("O banco já tem dados. Migração cancelada.")
            return

        veiculos = {}
        for d in dados["veiculos"]:
            v = Veiculo(
                placa=d["placa"],
                tipo=d["tipo"],
                modelo=d["modelo"],
                ano=d["ano"],
                diaria=Decimal(str(d["diaria"])),
                disponivel=d["disponivel"],
                portas=d.get("portas"),
                cilindrada=d.get("cilindrada"),
            )
            sessao.add(v)
            veiculos[v.placa] = v

        clientes = {}
        for d in dados["clientes"]:
            c = Cliente(nome=d["nome"], cpf=d["cpf"], idade=d["idade"], plano=d.get("plano_nome"))
            sessao.add(c)
            clientes[c.cpf] = c

        for d in dados["alugueis"]:
            cliente = clientes[d["cliente_cpf"]]
            veiculo = veiculos[d["veiculo_placa"]]
            sessao.add(
                Aluguel(
                    cliente=cliente,
                    veiculo=veiculo,
                    dias=d["dias"],
                    finalizado=d["finalizado"],
                    valor_final=calcula_valor_final(cliente, veiculo, d["dias"]),
                )
            )

        sessao.commit()
        print(
            f"Migrados: {len(veiculos)} veículos, {len(clientes)} clientes, "
            f"{len(dados['alugueis'])} aluguéis."
        )


if __name__ == "__main__":
    migra("estado.json")
