# observabilidade.py — logs em JSON com o número de cada pedido

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

# O número do pedido que está sendo atendido agora (ou "-" fora de um pedido).
id_do_pedido: ContextVar[str] = ContextVar("id_do_pedido", default="-")


class FormatoJSON(logging.Formatter):
    """Escreve cada linha de log como um objeto JSON."""

    def format(self, registro: logging.LogRecord) -> str:
        dados = {
            "quando": datetime.fromtimestamp(registro.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "nivel": registro.levelname,
            "mensagem": registro.getMessage(),
            "pedido": id_do_pedido.get(),
        }
        dados.update(getattr(registro, "campos", {}))
        if registro.exc_info:
            dados["erro"] = self.formatException(registro.exc_info)
        return json.dumps(dados, ensure_ascii=False)


def configura_logs(formato: str, nivel: str) -> None:
    saida = logging.StreamHandler()
    if formato == "json":
        saida.setFormatter(FormatoJSON())
    else:
        saida.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    raiz = logging.getLogger()
    raiz.handlers = [saida]
    raiz.setLevel(nivel)
