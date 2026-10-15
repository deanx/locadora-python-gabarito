# gera_dados_demo.py — um ano de aluguéis de mentira, para estudar análise de dados
# Use num banco de ESTUDO: ele acrescenta clientes, veículos e aluguéis.

import random
from datetime import date, timedelta
from decimal import Decimal

from banco import SessaoLocal
from modelos import Aluguel, Cliente, Veiculo
from planos import Plano
from servicos import calcula_multa, calcula_valor_final
from validadores import calcula_dv

random.seed(2026)

NOMES = [
    "Ana",
    "Bruno",
    "Carla",
    "Diego",
    "Elisa",
    "Fábio",
    "Gabi",
    "Heitor",
    "Íris",
    "João",
    "Kátia",
    "Lucas",
    "Marta",
    "Nuno",
    "Olga",
    "Paulo",
    "Quitéria",
    "Rafa",
    "Sara",
    "Tiago",
]
FROTA = [
    ("Carro", "Fiat Mobi", "79.90"),
    ("Carro", "Renault Kwid", "84.90"),
    ("Carro", "Chevrolet Onix", "120.50"),
    ("Carro", "Hyundai HB20", "135.00"),
    ("Carro", "VW T-Cross", "210.00"),
    ("Carro", "Jeep Compass", "280.00"),
    ("Moto", "Honda CG 160", "60.00"),
    ("Moto", "Yamaha Fazer 250", "95.00"),
    ("Moto", "Honda PCX", "70.00"),
    ("Moto", "BMW G 310", "160.00"),
]


def cpf(n: int) -> str:
    base = f"{700000000 + n:09d}"
    d1 = calcula_dv(base)
    d2 = calcula_dv(base + str(d1))
    return f"{base}{d1}{d2}"


def gera() -> None:
    with SessaoLocal() as sessao:
        clientes = []
        for i, nome in enumerate(NOMES):
            plano = random.choice([None, None, Plano.BRONZE, Plano.PRATA, Plano.OURO])
            c = Cliente(nome=f"{nome} Demo", cpf=cpf(i), idade=random.randint(21, 70), plano=plano)
            clientes.append(c)
        veiculos = []
        for i, (tipo, modelo, diaria) in enumerate(FROTA):
            placa = f"DEM{i}A{10 + i}"
            v = Veiculo(
                placa=placa,
                tipo=tipo,
                modelo=modelo,
                ano=random.randint(2020, 2025),
                diaria=Decimal(diaria),
            )
            veiculos.append(v)
        sessao.add_all(clientes)
        sessao.add_all(veiculos)
        sessao.flush()

        inicio_do_ano = date(2025, 10, 1)
        for _ in range(300):
            cliente = random.choice(clientes)
            veiculo = random.choice(veiculos)
            dias = random.choice([1, 2, 3, 3, 5, 5, 7, 7, 10, 14])
            inicio = inicio_do_ano + timedelta(days=random.randint(0, 364))
            aluguel = Aluguel(
                cliente=cliente,
                veiculo=veiculo,
                dias=dias,
                inicio=inicio,
                valor_final=calcula_valor_final(cliente, veiculo, dias),
            )
            atraso = random.choice([0, 0, 0, 0, 0, 0, 1, 2, 3])
            aluguel.devolucao = inicio + timedelta(days=dias + atraso)
            aluguel.finalizado = True
            aluguel.multa = calcula_multa(aluguel, aluguel.devolucao)
            sessao.add(aluguel)
        sessao.commit()
    print("Gerados: 20 clientes, 10 veículos, 300 aluguéis (out/2025 a set/2026).")


if __name__ == "__main__":
    gera()
