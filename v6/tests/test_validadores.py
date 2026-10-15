# tests/test_validadores.py — CPF e placa


def test_cpf_formatado_e_aceito(cliente_logado):
    novo = {"nome": "Diego Rocha", "cpf": "555.666.777-20", "idade": 30}
    resposta = cliente_logado.post("/clientes", json=novo)
    assert resposta.status_code == 201
    assert resposta.json()["cpf"] == "55566677720"


def test_cpf_com_digito_errado_da_422(cliente_logado):
    novo = {"nome": "Diego Rocha", "cpf": "555.666.777-88", "idade": 30}
    resposta = cliente_logado.post("/clientes", json=novo)
    assert resposta.status_code == 422
    assert "cpf: CPF inválido" in resposta.json()["detalhes"]


def test_placa_com_hifen_e_minuscula_e_aceita(cliente_gerente):
    novo = {"placa": "stu-9v01", "tipo": "Carro", "modelo": "VW Polo", "ano": 2024, "diaria": 150}
    resposta = cliente_gerente.post("/veiculos", json=novo)
    assert resposta.status_code == 201
    assert resposta.json()["placa"] == "STU9V01"
