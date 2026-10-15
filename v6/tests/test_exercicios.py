import pytest


def test_remove_veiculo_sem_alugueis(cliente_gerente):
    resposta = cliente_gerente.delete("/veiculos/MNO3P45")
    assert resposta.status_code == 204


def test_nao_remove_veiculo_com_alugueis(cliente_gerente):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 2}
    aluguel_id = cliente_gerente.post("/alugueis", json=pedido).json()["id"]
    cliente_gerente.post(f"/alugueis/{aluguel_id}/finalizar")
    resposta = cliente_gerente.delete("/veiculos/ABC1D23")
    assert resposta.status_code == 409


def test_finalizar_duas_vezes_da_409(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 2}
    aluguel_id = cliente_logado.post("/alugueis", json=pedido).json()["id"]
    cliente_logado.post(f"/alugueis/{aluguel_id}/finalizar")
    segunda = cliente_logado.post(f"/alugueis/{aluguel_id}/finalizar")
    assert segunda.status_code == 409


def test_endereco_inexistente(cliente_http):
    resposta = cliente_http.get("/nada")
    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "Endereço não encontrado"


def test_aluguel_curto_da_moto(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "MNO3P45", "dias": 3}
    resposta = cliente_logado.post("/alugueis", json=pedido)
    assert resposta.json()["valor_final"] == pytest.approx(162.0)


def test_tres_alugueis_viram_bronze(cliente_logado):
    nova = {"nome": "Diego Rocha", "cpf": "55566677720", "idade": 30}
    cliente_logado.post("/clientes", json=nova)
    for _ in range(3):
        pedido = {"cpf": "55566677720", "placa": "MNO3P45", "dias": 1}
        aluguel_id = cliente_logado.post("/alugueis", json=pedido).json()["id"]
        cliente_logado.post(f"/alugueis/{aluguel_id}/finalizar")
    assert cliente_logado.get("/clientes/55566677720").json()["plano"] == "Bronze"


def test_saude(cliente_http):
    resposta = cliente_http.get("/saude")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["banco"] == "ok"
