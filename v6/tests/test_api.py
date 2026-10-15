# tests/test_api.py — testes automatizados da API


def test_lista_veiculos(cliente_http):
    resposta = cliente_http.get("/veiculos")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_filtra_por_tipo(cliente_http):
    resposta = cliente_http.get("/veiculos", params={"tipo": "Moto"})
    placas = [v["placa"] for v in resposta.json()]
    assert placas == ["MNO3P45"]


def test_veiculo_inexistente_da_404(cliente_http):
    resposta = cliente_http.get("/veiculos/ZZZ9Z99")
    assert resposta.status_code == 404
    assert "não encontrado" in resposta.json()["erro"]


def test_cadastra_veiculo(cliente_gerente):
    novo = {"placa": "STU9V01", "tipo": "Carro", "modelo": "VW Polo", "ano": 2024, "diaria": 150.0}
    resposta = cliente_gerente.post("/veiculos", json=novo)
    assert resposta.status_code == 201
    assert resposta.json()["disponivel"] is True


def test_placa_repetida_da_409(cliente_gerente):
    repetido = {"placa": "ABC1D23", "tipo": "Carro", "modelo": "Outro", "ano": 2020, "diaria": 99.0}
    resposta = cliente_gerente.post("/veiculos", json=repetido)
    assert resposta.status_code == 409


def test_diaria_negativa_da_422(cliente_gerente):
    invalido = {
        "placa": "STU9V01",
        "tipo": "Carro",
        "modelo": "VW Polo",
        "ano": 2024,
        "diaria": -10,
    }
    resposta = cliente_gerente.post("/veiculos", json=invalido)
    assert resposta.status_code == 422


def test_aluguel_com_plano_prata(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 5}
    resposta = cliente_logado.post("/alugueis", json=pedido)
    assert resposta.status_code == 201
    # 120,50 x 5 = 602,50 ; menos 10% do plano Prata = 542,25
    assert resposta.json()["valor_final"] == 542.25


def test_aluguel_longo_tem_desconto_de_dias(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "MNO3P45", "dias": 7}
    resposta = cliente_logado.post("/alugueis", json=pedido)
    # 60 x 7 = 420 ; -10% por 7+ dias = 378 ; -10% Prata = 340,20
    assert resposta.json()["valor_final"] == 340.2


def test_veiculo_alugado_nao_aluga_de_novo(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 2}
    cliente_logado.post("/alugueis", json=pedido)
    segunda = cliente_logado.post("/alugueis", json=pedido)
    assert segunda.status_code == 409


def test_menor_de_idade_nao_aluga(cliente_logado):
    pedido = {"cpf": "11122233344", "placa": "ABC1D23", "dias": 2}
    resposta = cliente_logado.post("/alugueis", json=pedido)
    assert resposta.status_code == 409
    assert "menor de idade" in resposta.json()["erro"]


def test_finalizar_devolve_o_veiculo(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 2}
    aluguel_id = cliente_logado.post("/alugueis", json=pedido).json()["id"]
    resposta = cliente_logado.post(f"/alugueis/{aluguel_id}/finalizar")
    assert resposta.json()["finalizado"] is True
    assert cliente_logado.get("/veiculos/ABC1D23").json()["disponivel"] is True


def test_validacao_em_portugues(cliente_gerente):
    invalido = {"placa": "abc", "tipo": "Barco", "modelo": "X", "ano": 2020, "diaria": 10}
    resposta = cliente_gerente.post("/veiculos", json=invalido)
    assert resposta.status_code == 422
    assert "placa: formato inválido" in resposta.json()["detalhes"]


def test_patch_com_diaria_nula_nao_quebra(cliente_gerente):
    # Bug da Aula 51: diaria null derrubava a API com 500
    resposta = cliente_gerente.patch("/veiculos/ABC1D23", json={"diaria": None})
    assert resposta.status_code == 200
    assert resposta.json()["diaria"] == 120.5
