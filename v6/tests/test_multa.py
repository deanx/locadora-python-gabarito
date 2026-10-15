# tests/test_multa.py — testes da devolução com data e multa


def aluga_onix(cliente_logado, inicio="2026-10-01", dias=5):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": dias, "inicio": inicio}
    return cliente_logado.post("/alugueis", json=pedido).json()


def test_aluguel_mostra_devolucao_prevista(cliente_logado):
    aluguel = aluga_onix(cliente_logado)
    assert aluguel["inicio"] == "2026-10-01"
    assert aluguel["devolucao_prevista"] == "2026-10-06"


def test_devolucao_no_prazo_sem_multa(cliente_logado):
    aluguel = aluga_onix(cliente_logado)
    resposta = cliente_logado.post(
        f"/alugueis/{aluguel['id']}/finalizar", json={"data": "2026-10-06"}
    )
    assert resposta.json()["multa"] == 0.0


def test_devolucao_adiantada_sem_multa(cliente_logado):
    aluguel = aluga_onix(cliente_logado)
    resposta = cliente_logado.post(
        f"/alugueis/{aluguel['id']}/finalizar", json={"data": "2026-10-03"}
    )
    assert resposta.json()["multa"] == 0.0


def test_dois_dias_de_atraso(cliente_logado):
    aluguel = aluga_onix(cliente_logado)
    resposta = cliente_logado.post(
        f"/alugueis/{aluguel['id']}/finalizar", json={"data": "2026-10-08"}
    )
    # 2 dias x 120,50 x 1,20 = 289,20
    assert resposta.json()["multa"] == 289.2
    assert resposta.json()["devolucao"] == "2026-10-08"


def test_devolucao_antes_do_inicio_da_409(cliente_logado):
    aluguel = aluga_onix(cliente_logado)
    resposta = cliente_logado.post(
        f"/alugueis/{aluguel['id']}/finalizar", json={"data": "2026-09-30"}
    )
    assert resposta.status_code == 409


def test_finalizar_sem_corpo_usa_hoje(cliente_logado):
    from datetime import date

    hoje = date.today().isoformat()
    aluguel = aluga_onix(cliente_logado, inicio=hoje)
    resposta = cliente_logado.post(f"/alugueis/{aluguel['id']}/finalizar")
    assert resposta.status_code == 200
    assert resposta.json()["devolucao"] == hoje
    assert resposta.json()["multa"] == 0.0


def test_data_invalida_da_422(cliente_logado):
    aluguel = aluga_onix(cliente_logado)
    resposta = cliente_logado.post(
        f"/alugueis/{aluguel['id']}/finalizar", json={"data": "08/10/2026"}
    )
    assert resposta.status_code == 422
