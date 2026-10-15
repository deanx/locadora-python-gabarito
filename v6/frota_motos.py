# frota_motos.py — vale a pena comprar mais motos? (análise do caderno do Módulo 10)

import sys

import pandas as pd
from sqlalchemy import create_engine

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", None)

DIAS_DO_PERIODO = 365


def analisa(url_banco: str) -> pd.DataFrame:
    motor = create_engine(url_banco)
    alugueis = pd.read_sql(
        """
        SELECT v.placa, v.tipo, a.dias, a.valor_final + a.multa AS total
        FROM alugueis a JOIN veiculos v ON v.id = a.veiculo_id
        """,
        motor,
    )
    frota = pd.read_sql("SELECT placa, tipo FROM veiculos", motor)

    por_veiculo = alugueis.groupby("placa").agg(dias=("dias", "sum"), total=("total", "sum"))
    por_veiculo = frota.set_index("placa").join(por_veiculo).fillna(0)

    resumo = por_veiculo.groupby("tipo").agg(
        veiculos=("dias", "size"),
        dias_alugados=("dias", "sum"),
        faturamento=("total", "sum"),
    )
    resumo["ocupacao_pct"] = (
        resumo["dias_alugados"] / (resumo["veiculos"] * DIAS_DO_PERIODO) * 100
    ).round(1)
    resumo["faturamento_por_veiculo"] = (resumo["faturamento"] / resumo["veiculos"]).round(2)
    resumo["faturamento_por_dia_alugado"] = (resumo["faturamento"] / resumo["dias_alugados"]).round(
        2
    )
    return resumo


if __name__ == "__main__":
    print(analisa(sys.argv[1] if len(sys.argv) > 1 else "sqlite:///estudo.db"))
