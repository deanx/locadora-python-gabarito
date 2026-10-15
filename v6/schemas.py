# schemas.py — o formato dos dados que entram e saem da API

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from planos import Plano
from texto import normaliza_nome
from validadores import cpf_valido, normaliza_placa, so_digitos

# Dinheiro: Decimal com duas casas dentro do sistema; número no JSON.
Dinheiro = Annotated[
    Decimal,
    Field(max_digits=10, decimal_places=2),
    PlainSerializer(float, return_type=float, when_used="json"),
]


class VeiculoEntrada(BaseModel):
    placa: str = Field(pattern=r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

    @field_validator("placa", mode="before")
    @classmethod
    def limpa_placa(cls, valor: str) -> str:
        return normaliza_placa(valor) if isinstance(valor, str) else valor

    tipo: Literal["Carro", "Moto"]
    modelo: str = Field(min_length=2)
    ano: int = Field(ge=1990, le=2030)
    diaria: Dinheiro = Field(gt=0)
    portas: int | None = None
    cilindrada: int | None = None


class VeiculoAtualizacao(BaseModel):
    modelo: str | None = Field(default=None, min_length=2)
    ano: int | None = Field(default=None, ge=1990, le=2030)
    diaria: Dinheiro | None = Field(default=None, gt=0)


class VeiculoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    placa: str
    tipo: str
    modelo: str
    ano: int
    diaria: Dinheiro
    disponivel: bool


class ClienteEntrada(BaseModel):
    nome: str = Field(min_length=2)
    cpf: str
    idade: int = Field(ge=0, le=120)
    plano: Plano | None = None
    telefone: str | None = Field(default=None, pattern=r"^[0-9]{10,11}$")

    cep: str | None = None

    @field_validator("nome")
    @classmethod
    def normaliza(cls, valor: str) -> str:
        return normaliza_nome(valor)

    @field_validator("cpf", mode="before")
    @classmethod
    def limpa_cpf(cls, valor: str) -> str:
        return so_digitos(valor) if isinstance(valor, str) else valor

    @field_validator("cpf")
    @classmethod
    def confere_cpf(cls, cpf: str) -> str:
        if not cpf_valido(cpf):
            raise ValueError("CPF inválido")
        return cpf


class ClienteSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    cpf: str
    idade: int
    plano: str | None
    telefone: str | None
    cep: str | None = None
    cidade: str | None = None
    uf: str | None = None


class AluguelEntrada(BaseModel):
    cpf: str
    placa: str
    dias: int = Field(ge=1, le=30)
    inicio: date | None = None


class Devolucao(BaseModel):
    data: date | None = None


class AluguelSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dias: int
    valor_final: Dinheiro
    finalizado: bool
    inicio: date
    devolucao_prevista: date
    devolucao: date | None
    multa: Dinheiro
    cliente: ClienteSaida
    veiculo: VeiculoSaida


class Token(BaseModel):
    access_token: str
    token_type: str


class AtendenteSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    usuario: str
    nome: str


class EventoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quando: datetime
    usuario: str
    acao: str
    detalhe: str


class PerguntaAssistente(BaseModel):
    conversa: str | None = Field(default=None, max_length=32)
    mensagem: str = Field(min_length=1, max_length=1000)


class RespostaAssistente(BaseModel):
    conversa: str
    resposta: str


class Pagina[T](BaseModel):
    """Uma página de resultados, para qualquer tipo de item."""

    itens: list[T]
    pagina: int
    tamanho: int
    total: int


class Disponibilidade(BaseModel):
    placa: str
    inicio: date
    fim: date
    livre: bool
    conflitos: list[int]
