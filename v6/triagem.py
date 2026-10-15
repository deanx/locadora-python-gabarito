# triagem.py — a mensagem do cliente classificada, e o pedido extraído quando houver

from datetime import date
from typing import Literal

import anthropic
from anthropic.types import ToolParam
from pydantic import BaseModel, ValidationError

from config import MODELO_IA
from extracao import ExtracaoInvalida, PedidoExtraido, extrai_pedido

Categoria = Literal["novo_aluguel", "devolucao", "reclamacao", "duvida", "outro"]

PROXIMO_PASSO: dict[str, str] = {
    "novo_aluguel": "Conferir os dados e registrar o aluguel",
    "devolucao": "Agendar a vistoria da devolução",
    "reclamacao": "Encaminhar para a gerência",
    "duvida": "Responder pelo assistente ou por um atendente",
    "outro": "Ler e decidir",
}


class Classificacao(BaseModel):
    categoria: Categoria


CLASSIFICA: ToolParam = {
    "name": "classifica",
    "description": "Classifica a mensagem do cliente numa categoria.",
    "input_schema": Classificacao.model_json_schema(),
}


class Triagem(BaseModel):
    categoria: Categoria
    proximo_passo: str
    pedido: PedidoExtraido | None = None
    problema: str | None = None


def classifica(cliente: anthropic.Anthropic, mensagem: str) -> Categoria:
    resposta = cliente.messages.create(
        model=MODELO_IA,
        max_tokens=100,
        system="Classifique a mensagem de um cliente de uma locadora de veículos.",
        tools=[CLASSIFICA],
        tool_choice={"type": "tool", "name": "classifica"},
        messages=[{"role": "user", "content": mensagem}],
    )
    bloco = next((b for b in resposta.content if b.type == "tool_use"), None)
    if bloco is None:
        return "outro"
    try:
        return Classificacao.model_validate(bloco.input).categoria
    except ValidationError:
        return "outro"


def faz_triagem(cliente: anthropic.Anthropic, mensagem: str, hoje: date) -> Triagem:
    categoria = classifica(cliente, mensagem)
    triagem = Triagem(categoria=categoria, proximo_passo=PROXIMO_PASSO[categoria])
    if categoria == "novo_aluguel":
        try:
            triagem.pedido = extrai_pedido(cliente, mensagem, hoje)
        except ExtracaoInvalida as erro:
            triagem.problema = str(erro)
    return triagem
