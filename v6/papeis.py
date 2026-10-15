# papeis.py — os papéis de quem usa o sistema

from enum import StrEnum


class Papel(StrEnum):
    ATENDENTE = "atendente"
    GERENTE = "gerente"
    AUDITOR = "auditor"
