# moeda.py — formatação de valores em reais

from decimal import Decimal

from typing_extensions import deprecated


def formata_brl(valor: Decimal | float) -> str:
    formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


@deprecated("brl está obsoleta e sai na versão 2.0; use formata_brl")
def brl(valor: Decimal | float) -> str:
    return formata_brl(valor)
