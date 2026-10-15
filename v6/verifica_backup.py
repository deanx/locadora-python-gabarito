# verifica_backup.py — restaura uma cópia num banco descartável e confere

import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from faz_backup import url_para_ferramentas


def contagens(url: str) -> dict[str, int]:
    motor = create_engine(url)
    with motor.connect() as conexao:
        tabelas = sorted(inspect(motor).get_table_names())
        resultado = {
            t: conexao.execute(text(f'SELECT count(*) FROM "{t}"')).scalar_one() for t in tabelas
        }
    motor.dispose()
    return resultado


def verifica(copia: Path, url_origem: str, url_teste: str) -> bool:
    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--dbname",
            url_para_ferramentas(url_teste),
            str(copia),
        ],
        check=True,
    )
    origem, restaurado = contagens(url_origem), contagens(url_teste)
    tudo_certo = True
    for tabela in sorted(origem.keys() | restaurado.keys()):
        a, b = origem.get(tabela), restaurado.get(tabela)
        marca = "ok" if a == b else "DIFERENTE"
        tudo_certo = tudo_certo and a == b
        print(f"  {tabela:<16} origem={a}  cópia={b}  {marca}")
    return tudo_certo


if __name__ == "__main__":
    copia, url_origem, url_teste = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    if verifica(copia, url_origem, url_teste):
        print("Cópia verificada: restaurou e bate com a origem.")
    else:
        sys.exit("ATENÇÃO: a cópia não bate com a origem.")
