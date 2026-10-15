# importacao.py — importa clientes de uma planilha, tudo ou nada

import csv
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from banco import SessaoLocal
from modelos import Cliente
from schemas import ClienteEntrada


@dataclass
class ResultadoImportacao:
    importados: int = 0
    erros: list[str] = field(default_factory=list)


def importa_clientes_csv(caminho: Path) -> ResultadoImportacao:
    resultado = ResultadoImportacao()
    validos: list[ClienteEntrada] = []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for numero, registro in enumerate(csv.DictReader(arquivo), start=2):
            dados = {campo: valor for campo, valor in registro.items() if valor}
            try:
                validos.append(ClienteEntrada.model_validate(dados))
            except ValidationError as erro:
                campos = ", ".join(str(e["loc"][0]) for e in erro.errors())
                resultado.erros.append(f"linha {numero}: problema em {campos}")
    if resultado.erros:
        return resultado
    with SessaoLocal.begin() as sessao:
        sessao.add_all(Cliente(**c.model_dump()) for c in validos)
    resultado.importados = len(validos)
    return resultado
