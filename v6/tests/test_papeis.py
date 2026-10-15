# tests/test_papeis.py — quem pode o quê, e o registro de quem fez


def test_atendente_nao_cadastra_veiculo(cliente_logado):
    novo = {"placa": "STU9V01", "tipo": "Carro", "modelo": "VW Polo", "ano": 2024, "diaria": 150}
    resposta = cliente_logado.post("/veiculos", json=novo)
    assert resposta.status_code == 403
    assert resposta.json()["erro"] == "Seu papel não permite fazer isto"


def test_atendente_registra_aluguel(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 2}
    assert cliente_logado.post("/alugueis", json=pedido).status_code == 201


def test_auditoria_e_so_do_gerente(cliente_logado):
    assert cliente_logado.get("/auditoria").status_code == 403


def test_auditoria_registra_quem_fez(cliente_gerente):
    novo = {"placa": "STU9V01", "tipo": "Carro", "modelo": "VW Polo", "ano": 2024, "diaria": 150}
    cliente_gerente.post("/veiculos", json=novo)
    cliente_gerente.post("/alugueis", json={"cpf": "12345678909", "placa": "STU9V01", "dias": 2})
    eventos = cliente_gerente.get("/auditoria").json()
    assert [(e["usuario"], e["acao"]) for e in eventos] == [
        ("chefe", "aluguel.registrado"),
        ("chefe", "veiculo.cadastrado"),
    ]


def test_operacao_recusada_nao_deixa_evento(cliente_gerente):
    pedido = {"cpf": "11122233344", "placa": "ABC1D23", "dias": 2}  # Carla, 16 anos
    assert cliente_gerente.post("/alugueis", json=pedido).status_code == 409
    assert cliente_gerente.get("/auditoria").json() == []


def test_limite_negativo_da_422(cliente_gerente):
    # Bug do caderno do Módulo 9: no PostgreSQL, LIMIT -1 derrubava a API com 500
    resposta = cliente_gerente.get("/auditoria", params={"limite": -1})
    assert resposta.status_code == 422


def test_auditor_ve_auditoria(cliente_auditor):
    assert cliente_auditor.get("/auditoria").status_code == 200


def test_auditor_nao_opera(cliente_auditor):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 2}
    assert cliente_auditor.post("/alugueis", json=pedido).status_code == 403
    assert cliente_auditor.get("/clientes").status_code == 403
