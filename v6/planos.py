# planos.py — os planos de fidelidade da locadora

from decimal import Decimal
from enum import StrEnum


class Plano(StrEnum):
    BRONZE = "Bronze"
    PRATA = "Prata"
    OURO = "Ouro"

    @property
    def desconto(self) -> Decimal:
        match self:
            case Plano.BRONZE:
                return Decimal("0.05")
            case Plano.PRATA:
                return Decimal("0.10")
            case Plano.OURO:
                return Decimal("0.20")
