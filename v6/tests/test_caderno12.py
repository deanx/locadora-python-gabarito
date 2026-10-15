# tests/test_caderno12.py — disponibilidade, paginação e o número de consultas

from datetime import date
from decimal import Decimal

from sqlalchemy import event

from banco import SessaoLocal, engine
from modelos import Veiculo
from rentabilidade import desempenho_da_frota
from servicos import registra_aluguel


def test_disponibilidade_com_periodo(cliente_http):
    with SessaoLocal() as sessao:
        aluguel = registra_aluguel(sessao, "12345678909", "ABC1D23", 5, date(2026, 10, 10))
        numero = aluguel.id
    url = "/veiculos/ABC1D23/disponibilidade"
    cruza = cliente_http.get(url, params={"inicio": "2026-10-12", "fim": "2026-10-14"}).json()
    depois = cliente_http.get(url, params={"inicio": "2026-10-15", "fim": "2026-10-18"}).json()
    assert (cruza["livre"], cruza["conflitos"]) == (False, [numero])
    assert (depois["livre"], depois["conflitos"]) == (True, [])


def test_periodo_invertido_da_422(cliente_http):
    params = {"inicio": "2026-10-15", "fim": "2026-10-10"}
    resposta = cliente_http.get("/veiculos/ABC1D23/disponibilidade", params=params)
    assert resposta.status_code == 422


def test_paginacao(cliente_http):
    with SessaoLocal() as sessao:
        sessao.add_all(
            Veiculo(
                placa=f"PAG{i}A{i:02d}",
                tipo="Carro",
                modelo="Teste",
                ano=2024,
                diaria=Decimal("100"),
            )
            for i in range(5)
        )
        sessao.commit()
    primeira = cliente_http.get("/veiculos-paginados", params={"tamanho": 3}).json()
    terceira = cliente_http.get("/veiculos-paginados", params={"pagina": 3, "tamanho": 3}).json()
    assert primeira["total"] == 7
    assert len(primeira["itens"]) == 3
    assert len(terceira["itens"]) == 1
    assert terceira["itens"][0]["placa"] == "PAG4A04"


def test_relatorio_faz_uma_consulta_so(cliente_http):
    with SessaoLocal() as sessao:
        sessao.add_all(
            Veiculo(
                placa=f"R{i:02d}A{i:03d}",
                tipo="Moto",
                modelo="Teste",
                ano=2024,
                diaria=Decimal("50"),
            )
            for i in range(30)
        )
        sessao.commit()
        consultas: list[str] = []

        def conta(*argumentos: object) -> None:
            consultas.append(str(argumentos[2]))

        event.listen(engine, "before_cursor_execute", conta)
        try:
            frota = desempenho_da_frota(sessao)
        finally:
            event.remove(engine, "before_cursor_execute", conta)
    assert len(frota) == 32
    assert len(consultas) == 1
