# auditoria.py — registro das operações importantes da locadora

import functools
import logging
import time
from collections import deque
from collections.abc import Callable

ULTIMAS_OPERACOES: deque[str] = deque(maxlen=50)


def auditado[**P, R](funcao: Callable[P, R]) -> Callable[P, R]:
    """Registra nome, duração e resultado (sucesso ou erro) de cada chamada."""

    @functools.wraps(funcao)
    def embrulho(*args: P.args, **kwargs: P.kwargs) -> R:
        inicio = time.perf_counter()
        try:
            resultado = funcao(*args, **kwargs)
        except Exception as erro:
            registro = f"{funcao.__name__}: FALHOU ({erro})"
            raise
        else:
            registro = f"{funcao.__name__}: ok"
            return resultado
        finally:
            duracao = (time.perf_counter() - inicio) * 1000
            linha = f"{registro} em {duracao:.1f} ms"
            ULTIMAS_OPERACOES.append(linha)
            logging.info(linha)

    return embrulho
