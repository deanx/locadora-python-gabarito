# enderecos.py — o endereço a partir do CEP, consultado num serviço externo

import asyncio
import logging

import httpx
from pydantic import BaseModel

from config import URL_SERVICO_CEP
from validadores import so_digitos

log = logging.getLogger("locadora.enderecos")

PRAZO_SEGUNDOS = 3.0
TENTATIVAS = 3


class Endereco(BaseModel):
    cep: str
    logradouro: str
    bairro: str
    cidade: str
    uf: str


class CepInvalido(Exception):
    pass


class CepNaoEncontrado(Exception):
    pass


class ServicoCepIndisponivel(Exception):
    pass


async def busca_endereco(cep: str) -> Endereco:
    """Consulta o serviço de CEP, com prazo e novas tentativas para falhas passageiras."""
    cep = so_digitos(cep)
    if len(cep) != 8:
        raise CepInvalido("O CEP precisa ter 8 dígitos")

    url = f"{URL_SERVICO_CEP}/{cep}/json/"
    async with httpx.AsyncClient(timeout=PRAZO_SEGUNDOS) as cliente:
        for tentativa in range(1, TENTATIVAS + 1):
            try:
                resposta = await cliente.get(url)
            except httpx.TransportError as erro:  # prazo estourado, conexão recusada...
                log.warning("CEP: tentativa %d falhou (%s)", tentativa, type(erro).__name__)
            else:
                if resposta.status_code == 400:
                    raise CepInvalido("O serviço recusou o formato do CEP")
                if resposta.status_code < 500:
                    resposta.raise_for_status()
                    return _converte(resposta.json(), cep)
                log.warning("CEP: tentativa %d recebeu %d", tentativa, resposta.status_code)
            if tentativa < TENTATIVAS:
                await asyncio.sleep(0.5 * tentativa)  # espera um pouco mais a cada vez
    raise ServicoCepIndisponivel("O serviço de CEP não respondeu")


def _converte(dados: dict, cep: str) -> Endereco:
    # O ViaCEP responde {"erro": "true"} (texto) para CEP inexistente; versões antigas usavam true.
    if dados.get("erro") in (True, "true"):
        raise CepNaoEncontrado(f"CEP {cep} não encontrado")
    return Endereco(
        cep=cep,
        logradouro=dados["logradouro"],
        bairro=dados["bairro"],
        cidade=dados["localidade"],
        uf=dados["uf"],
    )
