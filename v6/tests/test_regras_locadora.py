# test_regras_locadora.py — as regras do time também têm testes

from pathlib import Path

from ferramentas.regras_locadora import confere_texto

PRODUCAO = Path("v6/servicos.py")


def codigos(texto: str, caminho: Path = PRODUCAO) -> list[str]:
    return [achado.split(": ", 1)[1].split()[0] for achado in confere_texto(texto, caminho)]


def test_loc001_acusa_as_formas_de_float():
    texto = "\n".join(
        [
            "from decimal import Decimal",
            "import decimal",
            "a = Decimal(0.1)",
            "b = decimal.Decimal(-2.5)",
            "c = Decimal(float(x))",
        ]
    )
    assert codigos(texto) == ["LOC001", "LOC001", "LOC001"]


def test_loc001_nao_acusa_o_que_esta_certo():
    texto = 'from decimal import Decimal\na = Decimal("0.1")\nb = Decimal(7)\nc = "Decimal(0.1) num texto"\n'
    assert codigos(texto) == []


def test_loc002_acusa_print_em_producao():
    assert codigos('print("oi")\n') == ["LOC002"]


def test_loc002_isenta_scripts_testes_e_terminal():
    script = 'def main():\n    print("oi")\n\nif __name__ == "__main__":\n    main()\n'
    assert codigos(script) == []
    assert codigos('print("oi")\n', Path("v6/tests/test_x.py")) == []
    assert codigos('print("oi")\n', Path("v6/historico.py")) == []


def test_o_sistema_esta_limpo():
    arquivos = sorted(Path(__file__).resolve().parent.parent.glob("*.py"))
    achados = [
        a
        for arquivo in arquivos
        for a in confere_texto(arquivo.read_text(encoding="utf-8"), arquivo)
    ]
    assert achados == []
