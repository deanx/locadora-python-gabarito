# tests/test_recibos.py — o recibo gerado em segundo plano

from config import PASTA_RECIBOS


def test_aluguel_gera_recibo(cliente_logado):
    pedido = {"cpf": "12345678909", "placa": "ABC1D23", "dias": 5}
    aluguel = cliente_logado.post("/alugueis", json=pedido).json()
    recibo = PASTA_RECIBOS / f"recibo-{aluguel['id']}.txt"
    texto = recibo.read_text(encoding="utf-8")
    assert "Ana Silva" in texto
    assert "R$ 542,25" in texto
