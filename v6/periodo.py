# periodo.py — um período de aluguel imutável, que se compara e se cruza (Aula 85)
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Self


@dataclass(frozen=True, order=True)
class Periodo:
    inicio: date
    fim: date

    def __post_init__(self) -> None:
        if self.fim <= self.inicio:
            raise ValueError("O fim precisa ser depois do início")

    def __len__(self) -> int:
        return (self.fim - self.inicio).days

    def __contains__(self, dia: date) -> bool:
        return self.inicio <= dia < self.fim

    def __and__(self, outro: Self) -> Self | None:
        inicio, fim = max(self.inicio, outro.inicio), min(self.fim, outro.fim)
        return type(self)(inicio, fim) if inicio < fim else None

    def __add__(self, dias: int) -> Self:
        return type(self)(self.inicio, self.fim + timedelta(days=dias))
