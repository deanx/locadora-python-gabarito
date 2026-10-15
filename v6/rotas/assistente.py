# rotas/assistente.py — o assistente de IA e a triagem

import logging
import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from assistente import FERRAMENTAS_INTERNAS, FERRAMENTAS_PUBLICAS, Consumo, LimiteDeVoltas, responde
from config import PRECO_ENTRADA_IA, PRECO_SAIDA_IA
from dependencias import OPERACAO, gerente_logado, pega_sessao
from ia import cria_cliente
from modelos import MensagemAssistente
from schemas import PerguntaAssistente, RespostaAssistente
from servicos import OperacaoInvalida
from triagem import Triagem, faz_triagem

log = logging.getLogger("locadora")
router = APIRouter(tags=["assistente"])

MAXIMO_DE_FALAS = 20


def pega_cliente_ia() -> anthropic.Anthropic:
    return cria_cliente()


@router.post("/assistente", response_model=RespostaAssistente)
def conversa_com_assistente(
    dados: PerguntaAssistente,
    sessao: Session = Depends(pega_sessao),
    ia: anthropic.Anthropic = Depends(pega_cliente_ia),
) -> RespostaAssistente:
    conversa = dados.conversa or uuid.uuid4().hex
    consulta = select(MensagemAssistente).where(MensagemAssistente.conversa == conversa)
    anteriores = sessao.scalars(consulta.order_by(MensagemAssistente.id)).all()
    if len(anteriores) >= MAXIMO_DE_FALAS:
        raise OperacaoInvalida("Esta conversa ficou longa demais. Comece uma nova.")
    historico: list[Any] = [{"role": m.papel, "content": m.texto} for m in anteriores]
    historico.append({"role": "user", "content": dados.mensagem})
    consumo = Consumo()
    try:
        texto = responde(ia, sessao, historico, FERRAMENTAS_PUBLICAS, consumo)
    except (anthropic.APIError, LimiteDeVoltas) as erro:
        log.error("Assistente indisponível: %s", erro)
        raise HTTPException(
            status_code=503, detail="O assistente está indisponível. Tente de novo em instantes."
        ) from erro
    sessao.add_all(
        [
            MensagemAssistente(conversa=conversa, papel="user", texto=dados.mensagem),
            MensagemAssistente(
                conversa=conversa,
                papel="assistant",
                texto=texto,
                tokens_entrada=consumo.entrada,
                tokens_saida=consumo.saida,
            ),
        ]
    )
    sessao.commit()
    return RespostaAssistente(conversa=conversa, resposta=texto)


@router.get("/assistente/consumo", dependencies=[Depends(gerente_logado)])
def consumo_do_assistente(sessao: Session = Depends(pega_sessao)) -> dict[str, Any]:
    respostas, soma_entrada, soma_saida = sessao.execute(
        select(
            func.count(MensagemAssistente.id),
            func.coalesce(func.sum(MensagemAssistente.tokens_entrada), 0),
            func.coalesce(func.sum(MensagemAssistente.tokens_saida), 0),
        ).where(MensagemAssistente.papel == "assistant")
    ).one()
    entrada, saida = soma_entrada or 0, soma_saida or 0
    relatorio: dict[str, Any] = {
        "respostas": respostas,
        "tokens_entrada": entrada,
        "tokens_saida": saida,
    }
    if PRECO_ENTRADA_IA and PRECO_SAIDA_IA:
        custo = (entrada * Decimal(PRECO_ENTRADA_IA) + saida * Decimal(PRECO_SAIDA_IA)) / 1_000_000
        centesimo = Decimal("0.0001")
        relatorio["custo_dolares"] = str(custo.quantize(centesimo, rounding=ROUND_HALF_UP))
        if respostas:
            medio = (custo / respostas).quantize(centesimo, rounding=ROUND_HALF_UP)
            relatorio["custo_medio_por_resposta"] = str(medio)
    return relatorio


class PerguntaInterna(BaseModel):
    mensagem: str = Field(min_length=1, max_length=4000)


@router.post("/assistente/interno", response_model=RespostaAssistente, dependencies=OPERACAO)
def assistente_interno(
    dados: PerguntaInterna,
    sessao: Session = Depends(pega_sessao),
    ia: anthropic.Anthropic = Depends(pega_cliente_ia),
) -> RespostaAssistente:
    historico: list[Any] = [{"role": "user", "content": dados.mensagem}]
    try:
        texto = responde(ia, sessao, historico, FERRAMENTAS_INTERNAS)
    except (anthropic.APIError, LimiteDeVoltas) as erro:
        raise HTTPException(status_code=503, detail="O assistente está indisponível.") from erro
    return RespostaAssistente(conversa="interno", resposta=texto)


@router.post("/triagem", response_model=Triagem, dependencies=OPERACAO)
def triagem_de_mensagem(
    dados: PerguntaInterna, ia: anthropic.Anthropic = Depends(pega_cliente_ia)
) -> Triagem:
    try:
        return faz_triagem(ia, dados.mensagem, date.today())
    except anthropic.APIError as erro:
        raise HTTPException(status_code=503, detail="A triagem está indisponível.") from erro
