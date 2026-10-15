# tests/test_autenticacao.py — quem pode usar o quê


def test_login_correto_devolve_token(cliente_http):
    resposta = cliente_http.post(
        "/login", data={"username": "balcao", "password": "senha-de-teste"}
    )
    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"


def test_senha_errada_da_401(cliente_http):
    resposta = cliente_http.post("/login", data={"username": "balcao", "password": "errada"})
    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Usuário ou senha incorretos"


def test_frota_e_publica(cliente_http):
    assert cliente_http.get("/veiculos").status_code == 200


def test_clientes_exigem_login(cliente_http):
    resposta = cliente_http.get("/clientes")
    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Faça login para usar este endereço"


def test_cadastro_exige_login(cliente_http):
    novo = {"placa": "STU9V01", "tipo": "Carro", "modelo": "VW Polo", "ano": 2024, "diaria": 150.0}
    assert cliente_http.post("/veiculos", json=novo).status_code == 401


def test_token_falsificado_da_401(cliente_http):
    cliente_http.headers["Authorization"] = "Bearer um.token.inventado"
    resposta = cliente_http.get("/clientes")
    assert resposta.status_code == 401
    assert "Login inválido" in resposta.json()["erro"]


def test_eu_mostra_quem_esta_logado(cliente_logado):
    resposta = cliente_logado.get("/eu")
    assert resposta.json() == {"usuario": "balcao", "nome": "Atendente de Teste"}
