# tests/ia_falsa.py — um dublê da API do Claude, para testar sem chave e sem rede

import json
from typing import Any

import httpx2


def mensagem(conteudo: list[dict[str, Any]], parada: str = "end_turn") -> dict[str, Any]:
    """Uma resposta no formato da API de mensagens."""
    return {
        "id": "msg_teste",
        "type": "message",
        "role": "assistant",
        "model": "modelo-de-teste",
        "content": conteudo,
        "stop_reason": parada,
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


def texto(t: str) -> dict[str, Any]:
    return mensagem([{"type": "text", "text": t}])


def usa_ferramenta(nome: str, entrada: dict[str, Any], id_: str = "toolu_1") -> dict[str, Any]:
    return mensagem([{"type": "tool_use", "id": id_, "name": nome, "input": entrada}], "tool_use")


class IAFalsa:
    """Responde, em ordem, as mensagens roteirizadas; guarda o que recebeu."""

    def __init__(self, *respostas: dict[str, Any] | int) -> None:
        self.respostas = list(respostas)
        self.pedidos: list[dict[str, Any]] = []

    def _responde(self, pedido: httpx2.Request) -> httpx2.Response:
        self.pedidos.append(json.loads(pedido.content))
        resposta = self.respostas.pop(0)
        if isinstance(resposta, int):  # um código de erro HTTP, para simular falhas da API
            erro = {"type": "error", "error": {"type": "api_error", "message": "falha simulada"}}
            return httpx2.Response(resposta, json=erro)
        return httpx2.Response(200, json=resposta)

    def http_client(self) -> httpx2.Client:
        return httpx2.Client(transport=httpx2.MockTransport(self._responde))

    def cliente(self) -> Any:
        """Um cliente do SDK de verdade, ligado a este dublê."""
        from ia import cria_cliente

        return cria_cliente(self.http_client(), chave="chave-de-teste", tentativas=0)
