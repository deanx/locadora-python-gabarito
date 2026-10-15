# faz_backup.py — cópia de segurança do banco PostgreSQL, com data no nome

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from config import URL_BANCO


def url_para_ferramentas(url: str) -> str:
    """O pg_dump não entende o '+psycopg' do SQLAlchemy: 'postgresql+psycopg://' vira 'postgresql://'."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def faz_backup(pasta: Path) -> Path:
    if not URL_BANCO.startswith("postgresql"):
        sys.exit("Este script faz cópia de bancos PostgreSQL. Para o SQLite, copie o arquivo .db.")
    pasta.mkdir(parents=True, exist_ok=True)
    instante = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
    destino = pasta / f"locadora-{instante}.dump"
    subprocess.run(
        [
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--file",
            str(destino),
            url_para_ferramentas(URL_BANCO),
        ],
        check=True,
    )
    return destino


if __name__ == "__main__":
    caminho = faz_backup(Path("backups"))
    print(f"Cópia salva em {caminho} ({caminho.stat().st_size / 1024:.0f} KB)")
