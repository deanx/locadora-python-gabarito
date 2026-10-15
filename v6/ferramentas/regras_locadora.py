# regras_locadora.py — regras do código da locadora que o ruff não conhece (Aula 110)
#
#   LOC001  Decimal criado a partir de um float: Decimal(0.1), Decimal(float(x))
#   LOC002  print em código de produção (scripts e a interface de terminal são isentos)

import ast
import sys
from pathlib import Path

# Arquivos que existem para conversar com o terminal, e por isso podem usar print.
ARQUIVOS_DE_TERMINAL = {
    "historico.py": "mostra o histórico de um cliente no menu de terminal do sistema_v6",
}


def e_decimal(funcao: ast.expr) -> bool:
    if isinstance(funcao, ast.Name):
        return funcao.id == "Decimal"
    if isinstance(funcao, ast.Attribute):
        return funcao.attr == "Decimal"
    return False


def e_float(no: ast.expr) -> bool:
    """Um número com casas decimais escrito no código (0.1, -2.5) ou um float(...)."""
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, ast.USub):
        no = no.operand
    if isinstance(no, ast.Constant):
        return isinstance(no.value, float)
    return isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "float"


def e_script(arvore: ast.Module) -> bool:
    """O arquivo tem um if __name__ == "__main__": no nível do módulo?"""
    return any(
        isinstance(no, ast.If)
        and isinstance(no.test, ast.Compare)
        and isinstance(no.test.left, ast.Name)
        and no.test.left.id == "__name__"
        for no in arvore.body
    )


class Regras(ast.NodeVisitor):
    def __init__(self, confere_print: bool) -> None:
        self.confere_print = confere_print
        self.achados: list[tuple[int, int, str]] = []

    def visit_Call(self, no: ast.Call) -> None:
        if e_decimal(no.func) and no.args and e_float(no.args[0]):
            self.achados.append(
                (
                    no.lineno,
                    no.col_offset,
                    "LOC001 Decimal criado a partir de um float; escreva o número entre aspas",
                )
            )
        if self.confere_print and isinstance(no.func, ast.Name) and no.func.id == "print":
            self.achados.append(
                (no.lineno, no.col_offset, "LOC002 print em código de produção; use o logging")
            )
        self.generic_visit(no)


def confere_texto(texto: str, caminho: Path) -> list[str]:
    arvore = ast.parse(texto, filename=str(caminho))
    producao = "tests" not in caminho.parts and caminho.name not in ARQUIVOS_DE_TERMINAL
    regras = Regras(confere_print=producao and not e_script(arvore))
    regras.visit(arvore)
    return [
        f"{caminho}:{linha}:{coluna + 1}: {mensagem}" for linha, coluna, mensagem in regras.achados
    ]


def main(arquivos: list[str]) -> int:
    problemas = []
    for arquivo in arquivos:
        caminho = Path(arquivo)
        problemas += confere_texto(caminho.read_text(encoding="utf-8"), caminho)
    for problema in problemas:
        print(problema)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
