# versao.py — a versão do sistema, lida do pyproject.toml (Aula 104)

import logging
import tomllib
from pathlib import Path

log = logging.getLogger("locadora")

# O pyproject.toml mora na raiz do projeto, uma pasta acima da v6/.
PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def versao_do_projeto(caminho: Path = PYPROJECT) -> str:
    """Lê a versão do pyproject.toml. Se ele não estiver lá, avisa e segue."""
    try:
        with caminho.open("rb") as arquivo:
            versao = tomllib.load(arquivo)["project"]["version"]
    except (FileNotFoundError, KeyError):
        log.warning("Versão: não encontrei a versão em %s", caminho)
        return "desconhecida"
    if not isinstance(versao, str):
        log.warning("Versão: o valor em %s não é um texto: %r", caminho, versao)
        return "desconhecida"
    return versao


VERSAO = versao_do_projeto()
