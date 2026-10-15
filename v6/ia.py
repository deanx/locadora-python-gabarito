# ia.py — o cliente da API do Claude, configurado num lugar só

import anthropic
import httpx2

from config import CHAVE_IA, MODELO_IA

PRAZO_IA_SEGUNDOS = 30.0


def cria_cliente(
    http_client: httpx2.Client | None = None, chave: str | None = None, tentativas: int = 2
) -> anthropic.Anthropic:
    """Cria o cliente da API. Nos testes, recebe um http_client e uma chave de mentira."""
    return anthropic.Anthropic(
        api_key=chave or CHAVE_IA,
        timeout=PRAZO_IA_SEGUNDOS,
        max_retries=tentativas,
        http_client=http_client,
    )


def pergunta(cliente: anthropic.Anthropic, sistema: str, texto: str, max_tokens: int = 500) -> str:
    """Faz uma pergunta simples e devolve o texto da resposta."""
    resposta = cliente.messages.create(
        model=MODELO_IA,
        max_tokens=max_tokens,
        system=sistema,
        messages=[{"role": "user", "content": texto}],
    )
    return "".join(bloco.text for bloco in resposta.content if bloco.type == "text")
