# tests/test_regras.py — testes das regras de cálculo

from decimal import Decimal

from modelos import Veiculo


def test_cinco_dias_sem_desconto():
    onix = Veiculo(placa="ABC1D23", tipo="Carro", modelo="Onix", ano=2023, diaria=Decimal("120.50"))
    assert onix.calcula_valor(5) == Decimal("602.50")


def test_sete_dias_tem_desconto():
    onix = Veiculo(placa="ABC1D23", tipo="Carro", modelo="Onix", ano=2023, diaria=Decimal("120.50"))
    assert onix.calcula_valor(7) == Decimal("759.15")


def test_arredondamento_de_centavos():
    from dinheiro import arredonda

    assert arredonda(Decimal("2.675")) == Decimal("2.68")
    assert arredonda(Decimal("2.665")) == Decimal("2.67")
