# dinheiro.py — valores em reais, sem centavos fantasmas

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


def arredonda(valor: Decimal) -> Decimal:
    """Arredonda para centavos, do jeito que se aprende na escola (0,5 sobe)."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)
