# assistente.py — o modelo consulta a locadora através de ferramentas

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import anthropic
from anthropic.types import MessageParam, ToolParam
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import MODELO_IA
from modelos import Cliente, Veiculo
from moeda import formata_brl
from servicos import calcula_valor_final

log = logging.getLogger("locadora.assistente")

MAXIMO_DE_VOLTAS = 5

SISTEMA = """Você é o assistente de atendimento de uma locadora de veículos.
Responda em português, de forma curta e simpática.
Para qualquer informação sobre veículos, disponibilidade ou preços, use as
ferramentas: nunca invente veículos, placas ou valores. Se uma ferramenta não
trouxer a informação, diga que não sabe. Você não registra aluguéis: para isso,
o cliente fala com um atendente."""


class EntradaFrota(BaseModel):
    tipo: str | None = Field(default=None, description="'Carro' ou 'Moto'; vazio para todos")


class EntradaOrcamento(BaseModel):
    placa: str = Field(description="A placa do veículo, como veio da consulta da frota")
    dias: int = Field(ge=1, le=30, description="Quantos dias de aluguel")
    cpf: str | None = Field(default=None, description="CPF do cliente, se ele informou")


FERRAMENTAS: list[ToolParam] = [
    {
        "name": "consulta_frota",
        "description": "Lista os veículos disponíveis agora, com modelo, placa e diária.",
        "input_schema": EntradaFrota.model_json_schema(),
    },
    {
        "name": "calcula_orcamento",
        "description": "Calcula o valor de um aluguel, com os descontos do sistema.",
        "input_schema": EntradaOrcamento.model_json_schema(),
    },
]


class EntradaIdentificacao(BaseModel):
    cpf: str = Field(description="CPF que o cliente informou ao atendente")


def identifica_cliente(sessao: Session, entrada: EntradaIdentificacao) -> dict[str, str]:
    """Só o que o atendimento precisa: primeiro nome e plano. Nada de CPF, telefone ou endereço."""
    cpf = "".join(c for c in entrada.cpf if c.isdigit())
    cliente = sessao.scalar(select(Cliente).where(Cliente.cpf == cpf))
    if cliente is None:
        return {"encontrado": "não"}
    return {
        "encontrado": "sim",
        "primeiro_nome": cliente.nome.split()[0],
        "plano": cliente.plano or "sem plano",
    }


class EntradaOrcamentoPublico(BaseModel):
    model_config = {"extra": "forbid"}

    placa: str = Field(description="A placa do veículo, como veio da consulta da frota")
    dias: int = Field(ge=1, le=30, description="Quantos dias de aluguel")


# No atendimento público, ninguém se identifica: o orçamento não aceita CPF.
FERRAMENTAS_PUBLICAS: list[ToolParam] = [
    FERRAMENTAS[0],
    {
        "name": "orcamento_publico",
        "description": "Calcula o valor de um aluguel, sem descontos de plano.",
        "input_schema": EntradaOrcamentoPublico.model_json_schema(),
    },
]


@dataclass
class Consumo:
    """Os tokens gastos por uma resposta, somando todas as voltas."""

    entrada: int = 0
    saida: int = 0
    voltas: int = 0
    ferramentas: list[str] = field(default_factory=list)


# No atendimento interno, o cliente está na frente do atendente e pode ser identificado.
FERRAMENTAS_INTERNAS: list[ToolParam] = [
    *FERRAMENTAS,
    {
        "name": "identifica_cliente",
        "description": "Identifica o cliente pelo CPF: devolve só o primeiro nome e o plano.",
        "input_schema": EntradaIdentificacao.model_json_schema(),
    },
]


class LimiteDeVoltas(Exception):
    pass


def consulta_frota(sessao: Session, entrada: EntradaFrota) -> list[dict[str, str]]:
    consulta = select(Veiculo).where(Veiculo.disponivel == True).order_by(Veiculo.diaria)
    if entrada.tipo:
        consulta = consulta.where(Veiculo.tipo == entrada.tipo)
    return [
        {"placa": v.placa, "modelo": v.modelo, "tipo": v.tipo, "diaria": formata_brl(v.diaria)}
        for v in sessao.scalars(consulta)
    ]


def calcula_orcamento(sessao: Session, entrada: EntradaOrcamento) -> dict[str, str]:
    veiculo = sessao.scalar(select(Veiculo).where(Veiculo.placa == entrada.placa))
    if veiculo is None:
        raise ValueError(f"Não existe veículo com a placa {entrada.placa}")
    cliente = None
    if entrada.cpf:
        cliente = sessao.scalar(select(Cliente).where(Cliente.cpf == entrada.cpf))
    if cliente is not None:
        valor = calcula_valor_final(cliente, veiculo, entrada.dias)
        observacao = f"com o desconto do plano {cliente.plano}" if cliente.plano else "sem plano"
    else:
        valor = veiculo.calcula_valor(entrada.dias)
        observacao = "sem desconto de plano (cliente não identificado)"
    return {
        "veiculo": veiculo.modelo,
        "dias": str(entrada.dias),
        "valor": formata_brl(valor),
        "observacao": observacao,
    }


def executa(sessao: Session, nome: str, entrada: dict[str, Any], permitidas: set[str]) -> Any:
    """Roda a ferramenta pedida pelo modelo, validando a entrada como qualquer dado de fora."""
    if nome not in permitidas:
        raise ValueError(f"Ferramenta não permitida aqui: {nome}")
    if nome == "consulta_frota":
        return consulta_frota(sessao, EntradaFrota.model_validate(entrada))
    if nome == "calcula_orcamento":
        return calcula_orcamento(sessao, EntradaOrcamento.model_validate(entrada))
    if nome == "identifica_cliente":
        return identifica_cliente(sessao, EntradaIdentificacao.model_validate(entrada))
    if nome == "orcamento_publico":
        dados = EntradaOrcamentoPublico.model_validate(entrada)
        return calcula_orcamento(sessao, EntradaOrcamento(placa=dados.placa, dias=dados.dias))
    raise ValueError(f"Ferramenta desconhecida: {nome}")


def responde(
    cliente: anthropic.Anthropic,
    sessao: Session,
    historico: list[MessageParam],
    ferramentas: list[ToolParam] = FERRAMENTAS,
    consumo: Consumo | None = None,
) -> str:
    """Conversa com o modelo, executando as ferramentas que ele pedir, até a resposta final."""
    permitidas = {f["name"] for f in ferramentas}
    consumo = consumo if consumo is not None else Consumo()
    for _ in range(MAXIMO_DE_VOLTAS):
        resposta = cliente.messages.create(
            model=MODELO_IA,
            max_tokens=800,
            system=SISTEMA,
            tools=ferramentas,
            messages=historico,
        )
        consumo.voltas += 1
        consumo.entrada += resposta.usage.input_tokens
        consumo.saida += resposta.usage.output_tokens
        historico.append({"role": "assistant", "content": resposta.content})
        if resposta.stop_reason != "tool_use":
            return "".join(b.text for b in resposta.content if b.type == "text")

        resultados: list[Any] = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue
            consumo.ferramentas.append(bloco.name)
            try:
                saida = executa(sessao, bloco.name, bloco.input, permitidas)
                resultados.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloco.id,
                        "content": json.dumps(saida, ensure_ascii=False),
                    }
                )
            except (ValueError, ValidationError) as erro:
                log.warning("Ferramenta %s recusada: %s", bloco.name, erro)
                resultados.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloco.id,
                        "content": f"Erro: {erro}",
                        "is_error": True,
                    }
                )
        historico.append({"role": "user", "content": resultados})
    raise LimiteDeVoltas(f"O assistente passou de {MAXIMO_DE_VOLTAS} voltas sem responder")
