# tests/test_caderno8.py — os desafios do caderno do Módulo 8

from datetime import date
from decimal import Decimal
from pathlib import Path

from auditoria import ULTIMAS_OPERACOES
from banco import SessaoLocal
from importacao import importa_clientes_csv
from modelos import Cliente
from rentabilidade import desempenho_da_frota, faturamento_por_mes
from servicos import finaliza_aluguel, registra_aluguel


def test_auditoria_registra_sucesso_e_falha(cliente_http):
    ULTIMAS_OPERACOES.clear()
    with SessaoLocal() as sessao:
        registra_aluguel(sessao, "12345678909", "ABC1D23", 2)
        try:
            registra_aluguel(sessao, "12345678909", "ABC1D23", 2)
        except Exception:
            pass
    assert ULTIMAS_OPERACOES[0].startswith("registra_aluguel: ok")
    assert ULTIMAS_OPERACOES[1].startswith("registra_aluguel: FALHOU")


def test_importacao_valida(cliente_http, tmp_path: Path):
    arquivo = tmp_path / "clientes.csv"
    arquivo.write_text(
        "nome,cpf,idade,plano\n"
        "Diego Rocha,555.666.777-20,30,\n"
        "Elisa Prado,987.654.321-00,41,Ouro\n",
        encoding="utf-8",
    )
    resultado = importa_clientes_csv(arquivo)
    assert resultado.importados == 2
    with SessaoLocal() as sessao:
        assert sessao.query(Cliente).filter_by(cpf="98765432100").one().plano == "Ouro"


def test_importacao_com_erro_nao_grava_nada(cliente_http, tmp_path: Path):
    arquivo = tmp_path / "clientes.csv"
    arquivo.write_text(
        "nome,cpf,idade,plano\n"
        "Diego Rocha,555.666.777-20,30,\n"
        "Fulano,111.111.111-11,trinta,Diamante\n",
        encoding="utf-8",
    )
    resultado = importa_clientes_csv(arquivo)
    assert resultado.importados == 0
    assert resultado.erros == ["linha 3: problema em cpf, idade, plano"]
    with SessaoLocal() as sessao:
        assert sessao.query(Cliente).filter_by(cpf="55566677720").first() is None


def test_rentabilidade(cliente_http):
    with SessaoLocal() as sessao:
        aluguel = registra_aluguel(sessao, "12345678909", "ABC1D23", 5, date(2026, 9, 28))
        finaliza_aluguel(sessao, aluguel.id, date(2026, 10, 5))
        registra_aluguel(sessao, "12345678909", "MNO3P45", 3, date(2026, 10, 2))
        meses = faturamento_por_mes(sessao)
        frota = desempenho_da_frota(sessao)
    assert meses == {"2026-09": Decimal("542.25") + Decimal("289.20"), "2026-10": Decimal("162.00")}
    assert [(d.placa, d.classificacao) for d in frota] == [
        ("ABC1D23", "regular"),
        ("MNO3P45", "regular"),
    ]
