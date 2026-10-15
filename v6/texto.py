# texto.py — nomes que se comparam do jeito que as pessoas esperam (Aula 104)

import unicodedata


def sem_acento(texto: str) -> str:
    """Remove os acentos: separa letra e acento (NFD) e descarta os acentos."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def chave_busca(texto: str) -> str:
    """A forma de um texto para comparações: sem acento e sem maiúsculas."""
    return sem_acento(texto).casefold()


def normaliza_nome(nome: str) -> str:
    """A forma de um nome para guardar: espaços limpos e acentos juntos (NFC)."""
    return unicodedata.normalize("NFC", " ".join(nome.split()))
