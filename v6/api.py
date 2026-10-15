# api.py — a locadora como uma API REST: o app, o middleware, os erros e as rotas

import logging
import time
import uuid
from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import FORMATO_LOG, NIVEL_LOG, NOME_LOCADORA
from observabilidade import configura_logs, id_do_pedido
from rotas import (
    alugueis,
    assistente,
    auditoria,
    autenticacao,
    clientes,
    enderecos,
    sistema,
    veiculos,
)
from rotas.assistente import pega_cliente_ia
from servicos import NaoEncontrado, OperacaoInvalida
from versao import VERSAO

configura_logs(FORMATO_LOG, NIVEL_LOG)
log = logging.getLogger("locadora")
app = FastAPI(title=NOME_LOCADORA, description="API da locadora de veículos", version=VERSAO)


@app.middleware("http")
async def registra_pedido(request: Request, proximo):
    numero = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    id_do_pedido.set(numero)
    inicio = time.perf_counter()
    resposta = await proximo(request)
    duracao = round((time.perf_counter() - inicio) * 1000, 1)
    resposta.headers["X-Request-ID"] = numero
    log.info(
        "pedido atendido",
        extra={
            "campos": {
                "metodo": request.method,
                "caminho": request.url.path,
                "status": resposta.status_code,
                "ms": duracao,
            }
        },
    )
    return resposta


@app.exception_handler(NaoEncontrado)
def trata_nao_encontrado(request: Request, erro: NaoEncontrado) -> JSONResponse:
    return JSONResponse(status_code=404, content={"erro": str(erro)})


@app.exception_handler(OperacaoInvalida)
def trata_operacao_invalida(request: Request, erro: OperacaoInvalida) -> JSONResponse:
    return JSONResponse(status_code=409, content={"erro": str(erro)})


@app.exception_handler(StarletteHTTPException)
def trata_http(request: Request, erro: StarletteHTTPException) -> JSONResponse:
    mensagens = {
        "Not Found": "Endereço não encontrado",
        "Method Not Allowed": "Método não permitido neste endereço",
        "Not authenticated": "Faça login para usar este endereço",
    }
    texto = mensagens.get(str(erro.detail), str(erro.detail))
    return JSONResponse(
        status_code=erro.status_code,
        content={"erro": texto},
        headers=getattr(erro, "headers", None),
    )


TRADUCOES = {
    "missing": "campo obrigatório",
    "greater_than": "deve ser maior que {gt}",
    "greater_than_equal": "deve ser maior ou igual a {ge}",
    "less_than_equal": "deve ser menor ou igual a {le}",
    "string_too_short": "deve ter pelo menos {min_length} caracteres",
    "string_pattern_mismatch": "formato inválido",
    "literal_error": "deve ser um destes valores: {expected}",
    "enum": "deve ser um destes valores: {expected}",
    "value_error": "{error}",
    "int_parsing": "deve ser um número inteiro",
    "float_parsing": "deve ser um número",
    "decimal_parsing": "deve ser um número",
    "decimal_max_places": "deve ter no máximo {decimal_places} casas decimais",
    "decimal_max_digits": "deve ter no máximo {max_digits} dígitos",
    "bool_parsing": "deve ser true ou false",
    "date_from_datetime_parsing": "deve ser uma data no formato AAAA-MM-DD",
    "date_parsing": "deve ser uma data no formato AAAA-MM-DD",
    "json_invalid": "o corpo não é um JSON válido",
    "model_attributes_type": "o corpo deve ser um objeto JSON",
}


def traduz(problema: dict) -> str:
    modelo = TRADUCOES.get(problema["type"])
    if modelo is None:
        return problema["msg"]
    contexto = {}
    for chave, valor in problema.get("ctx", {}).items():
        if isinstance(valor, (float, Decimal)) and valor == int(valor):
            valor = int(valor)
        if isinstance(valor, str):
            valor = valor.replace(" or ", " ou ")
        contexto[chave] = valor
    return modelo.format(**contexto)


@app.exception_handler(RequestValidationError)
def trata_validacao(request: Request, erro: RequestValidationError) -> JSONResponse:
    detalhes = []
    for problema in erro.errors():
        if problema["type"] == "json_invalid":
            campo = "corpo"
        else:
            campo = ".".join(str(parte) for parte in problema["loc"][1:]) or "corpo"
        detalhes.append(f"{campo}: {traduz(problema)}")
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos", "detalhes": detalhes})


@app.exception_handler(Exception)
def trata_inesperado(request: Request, erro: Exception) -> JSONResponse:
    log.error("Erro inesperado em %s %s", request.method, request.url.path, exc_info=erro)
    numero = id_do_pedido.get()
    return JSONResponse(
        status_code=500,
        content={"erro": f"Erro interno. Já fomos avisados. Código do pedido: {numero}"},
        headers={"X-Request-ID": numero},
    )


# --- as rotas, um arquivo por recurso (rotas/) ---
app.include_router(autenticacao.router)
app.include_router(sistema.router)
app.include_router(veiculos.router)
app.include_router(clientes.router)
app.include_router(alugueis.router)
app.include_router(enderecos.router)
app.include_router(assistente.router)
app.include_router(auditoria.router)

# os testes trocam a IA por um dublê pelo dependency_overrides, que localiza
# a dependência pela própria função: por isso ela continua acessível como api.pega_cliente_ia
__all__ = ["app", "pega_cliente_ia"]
