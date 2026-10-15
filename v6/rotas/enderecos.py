# rotas/enderecos.py — a consulta de CEP

from fastapi import APIRouter, HTTPException

from dependencias import OPERACAO
from enderecos import (
    CepInvalido,
    CepNaoEncontrado,
    Endereco,
    ServicoCepIndisponivel,
    busca_endereco,
)

router = APIRouter(tags=["endereços"])


@router.get("/enderecos/{cep}", response_model=Endereco, dependencies=OPERACAO)
async def consulta_endereco(cep: str) -> Endereco:
    try:
        return await busca_endereco(cep)
    except CepInvalido as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except CepNaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    except ServicoCepIndisponivel as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro
