# rotas/clientes.py — o recurso /clientes

import logging

import anyio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from dependencias import OPERACAO, pega_sessao
from enderecos import CepInvalido, CepNaoEncontrado, ServicoCepIndisponivel, busca_endereco
from modelos import Cliente
from schemas import ClienteEntrada, ClienteSaida
from servicos import OperacaoInvalida, busca_cliente
from texto import chave_busca

log = logging.getLogger("locadora")
router = APIRouter(tags=["clientes"])


@router.get("/clientes", response_model=list[ClienteSaida], dependencies=OPERACAO)
def lista_clientes(busca: str | None = None, sessao: Session = Depends(pega_sessao)):
    consulta = select(Cliente).order_by(Cliente.nome)
    if busca:
        consulta = consulta.where(Cliente.nome_busca.contains(chave_busca(busca)))
    return sessao.scalars(consulta).all()


@router.get("/clientes/{cpf}", response_model=ClienteSaida, dependencies=OPERACAO)
def detalha_cliente(cpf: str, sessao: Session = Depends(pega_sessao)):
    return busca_cliente(sessao, cpf)


@router.post(
    "/clientes",
    response_model=ClienteSaida,
    status_code=status.HTTP_201_CREATED,
    dependencies=OPERACAO,
)
def cadastra_cliente(dados: ClienteEntrada, sessao: Session = Depends(pega_sessao)):
    existe = sessao.scalar(select(Cliente).where(Cliente.cpf == dados.cpf))
    if existe is not None:
        raise OperacaoInvalida(f"Já existe um cliente com o CPF {dados.cpf}")
    cliente = Cliente(**dados.model_dump())
    if dados.cep is not None:
        try:
            endereco = anyio.from_thread.run(busca_endereco, dados.cep)
        except CepInvalido as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
        except CepNaoEncontrado as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
        except ServicoCepIndisponivel:
            # O cadastro não depende do CEP: grava sem endereço e registra
            log.warning("Cliente %s cadastrado sem endereço: serviço de CEP fora", dados.cpf)
            cliente.cep = dados.cep
        else:
            cliente.cep = endereco.cep
            cliente.logradouro = endereco.logradouro
            cliente.cidade = endereco.cidade
            cliente.uf = endereco.uf
    sessao.add(cliente)
    sessao.commit()
    return cliente
