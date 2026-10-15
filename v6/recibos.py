# recibos.py — o recibo do aluguel, gerado em segundo plano

import logging
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from config import ATRASO_RECIBO, PASTA_RECIBOS
from moeda import formata_brl

log = logging.getLogger("locadora.recibos")


@dataclass(frozen=True)
class DadosRecibo:
    """Uma cópia simples dos dados, independente da sessão do banco."""

    numero: int
    cliente: str
    placa: str
    modelo: str
    dias: int
    inicio: date
    valor: Decimal


def envia_recibo(dados: DadosRecibo) -> None:
    """Monta o recibo e o 'envia' (aqui: grava na caixa de saída). Leva alguns segundos."""
    try:
        time.sleep(ATRASO_RECIBO)  # finge a demora de um serviço de e-mail
        PASTA_RECIBOS.mkdir(parents=True, exist_ok=True)
        texto = (
            f"Recibo do aluguel #{dados.numero}\n"
            f"Cliente: {dados.cliente}\n"
            f"Veículo: {dados.placa} {dados.modelo}\n"
            f"Início: {dados.inicio.strftime('%d/%m/%Y')}, {dados.dias} dias\n"
            f"Valor: {formata_brl(dados.valor)}\n"
        )
        (PASTA_RECIBOS / f"recibo-{dados.numero}.txt").write_text(texto, encoding="utf-8")
        log.info("Recibo do aluguel #%d enviado", dados.numero)
    except Exception:
        log.exception("Falha ao enviar o recibo do aluguel #%d", dados.numero)
