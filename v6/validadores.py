# validadores.py — regras de formato de CPF e placa

import re

PLACA = re.compile(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}")


def so_digitos(texto: str) -> str:
    """Tira tudo o que não é dígito: '123.456.789-09' vira '12345678909'."""
    return re.sub(r"[^0-9]", "", texto)


def normaliza_placa(texto: str) -> str:
    """Aceita 'abc-1d23', 'ABC 1D23'... e devolve 'ABC1D23'."""
    return re.sub(r"[\s-]", "", texto).upper()


def placa_valida(placa: str) -> bool:
    return PLACA.fullmatch(placa) is not None


def calcula_dv(digitos: str) -> int:
    """Calcula um dígito verificador do CPF (o mesmo do caderno do Módulo 2)."""
    pesos = range(len(digitos) + 1, 1, -1)
    soma = sum(int(d) * p for d, p in zip(digitos, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    if not re.fullmatch(r"[0-9]{11}", cpf) or len(set(cpf)) == 1:
        return False
    return calcula_dv(cpf[:9]) == int(cpf[9]) and calcula_dv(cpf[:10]) == int(cpf[10])
