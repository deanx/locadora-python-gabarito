# extracao.py — o pedido do cliente, em texto livre, vira dados validados

from datetime import date
from typing import Literal, Self

import anthropic
from anthropic.types import ToolParam
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from config import MODELO_IA
from validadores import cpf_valido, so_digitos

SISTEMA = """Você extrai pedidos de aluguel de mensagens de clientes de uma locadora.
Hoje é {hoje}. Converta datas relativas ("amanhã", "dia 10") para datas completas.
Nunca invente dados: o que a mensagem não disser fica vazio, e vai para "duvidas"
como uma pergunta curta para o cliente. Não calcule valores."""


class PedidoExtraido(BaseModel):
    nome: str | None = Field(default=None, description="Nome do cliente, se ele disser")
    cpf: str | None = Field(default=None, description="CPF, só os dígitos, se ele disser")
    tipo: Literal["Carro", "Moto"] | None = Field(default=None, description="O que ele quer alugar")
    inicio: date | None = Field(default=None, description="Data de retirada")
    fim: date | None = Field(default=None, description="Data de devolução")
    duvidas: list[str] = Field(default_factory=list, description="O que falta perguntar")

    @field_validator("cpf", mode="before")
    @classmethod
    def limpa_cpf(cls, valor: object) -> object:
        return so_digitos(valor) if isinstance(valor, str) else valor

    @field_validator("cpf")
    @classmethod
    def confere_cpf(cls, cpf: str | None) -> str | None:
        if cpf is not None and not cpf_valido(cpf):
            raise ValueError("CPF inválido")
        return cpf

    @model_validator(mode="after")
    def confere_datas(self) -> Self:
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValueError("A devolução precisa ser depois da retirada")
        return self

    @property
    def dias(self) -> int | None:
        """Calculado pelo Python, nunca pelo modelo."""
        if self.inicio and self.fim:
            return (self.fim - self.inicio).days
        return None


FERRAMENTA: ToolParam = {
    "name": "registra_pedido",
    "description": "Registra os dados de um pedido de aluguel extraídos da mensagem.",
    "input_schema": PedidoExtraido.model_json_schema(),
}


class ExtracaoInvalida(Exception):
    pass


def extrai_pedido(cliente: anthropic.Anthropic, mensagem: str, hoje: date) -> PedidoExtraido:
    resposta = cliente.messages.create(
        model=MODELO_IA,
        max_tokens=500,
        system=SISTEMA.format(hoje=hoje.isoformat()),
        tools=[FERRAMENTA],
        tool_choice={"type": "tool", "name": "registra_pedido"},
        messages=[{"role": "user", "content": mensagem}],
    )
    bloco = next((b for b in resposta.content if b.type == "tool_use"), None)
    if bloco is None:
        raise ExtracaoInvalida("O modelo não devolveu o pedido estruturado")
    try:
        return PedidoExtraido.model_validate(bloco.input)
    except ValidationError as erro:
        raise ExtracaoInvalida(f"O pedido extraído não passou na validação: {erro}") from erro
