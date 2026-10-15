def test_api_recusa_cpf_em_outro_alfabeto(cliente_logado):
    arabe = "".join(chr(0x0660 + int(d)) for d in "52998224725")
    resposta = cliente_logado.post("/clientes", json={"nome": "Teste", "cpf": arabe, "idade": 30})
    assert resposta.status_code == 422


def test_lista_alugueis_com_cliente_e_veiculo(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 5}
    criado = cliente_logado.post("/alugueis", json=pedido).json()
    todos = cliente_logado.get("/alugueis").json()
    assert [a["id"] for a in todos] == [criado["id"]]
    assert todos[0]["cliente"]["nome"] == "Ana Silva"
    assert todos[0]["veiculo"]["placa"] == "ABC1D23"


def test_lista_so_os_ativos(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 5}
    criado = cliente_logado.post("/alugueis", json=pedido).json()
    assert cliente_logado.post(f"/alugueis/{criado['id']}/finalizar").status_code == 200
    assert len(cliente_logado.get("/alugueis").json()) == 1
    assert cliente_logado.get("/alugueis", params={"ativos": True}).json() == []
