# modelos.py — as tabelas do banco, descritas como classes

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from banco import Base
from moeda import formata_brl
from texto import chave_busca


class Veiculo(Base):
    __tablename__ = "veiculos"
    __table_args__ = (
        CheckConstraint("tipo IN ('Carro', 'Moto')", name="ck_veiculos_tipo"),
        CheckConstraint("diaria >= 0", name="ck_veiculos_diaria"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    placa: Mapped[str] = mapped_column(String(7), unique=True)
    tipo: Mapped[str] = mapped_column(String(5))
    modelo: Mapped[str]
    ano: Mapped[int]
    diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    disponivel: Mapped[bool] = mapped_column(default=True)
    portas: Mapped[int | None]
    cilindrada: Mapped[int | None]

    alugueis: Mapped[list["Aluguel"]] = relationship(back_populates="veiculo")

    def calcula_valor(self, dias: int) -> Decimal:
        valor = self.diaria * dias
        if dias >= 7:
            valor = valor * Decimal("0.90")
        return valor

    def __str__(self) -> str:
        status = "livre" if self.disponivel else "alugado"
        return f"{self.placa}: {self.modelo} ({self.ano}) — {formata_brl(self.diaria)} ({status})"


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    nome_busca: Mapped[str] = mapped_column(index=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    idade: Mapped[int]
    plano: Mapped[str | None]
    telefone: Mapped[str | None] = mapped_column(String(15))
    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None]
    cidade: Mapped[str | None]
    uf: Mapped[str | None] = mapped_column(String(2))

    alugueis: Mapped[list["Aluguel"]] = relationship(back_populates="cliente")

    @validates("nome")
    def _preenche_nome_busca(self, chave: str, nome: str) -> str:
        self.nome_busca = chave_busca(nome)
        return nome

    def pode_alugar(self) -> bool:
        return self.idade >= 18

    def __str__(self) -> str:
        texto = f"{self.nome} (CPF {self.cpf})"
        if self.plano is not None:
            texto += f" — Plano {self.plano}"
        return texto


class Aluguel(Base):
    __tablename__ = "alugueis"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"))
    dias: Mapped[int]
    valor_final: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    finalizado: Mapped[bool] = mapped_column(default=False)
    inicio: Mapped[date] = mapped_column(default=date.today)
    devolucao: Mapped[date | None]
    multa: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    @property
    def devolucao_prevista(self) -> date:
        return self.inicio + timedelta(days=self.dias)

    cliente: Mapped[Cliente] = relationship(back_populates="alugueis")
    veiculo: Mapped[Veiculo] = relationship(back_populates="alugueis")

    def __str__(self) -> str:
        estado = "finalizado" if self.finalizado else "em andamento"
        return (
            f"#{self.id} {self.cliente.nome} → {self.veiculo.placa}, "
            f"{self.dias} dias, {formata_brl(self.valor_final)} ({estado})"
        )


class Atendente(Base):
    __tablename__ = "atendentes"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(30), unique=True)
    nome: Mapped[str]
    senha_hash: Mapped[str]
    papel: Mapped[str] = mapped_column(String(20), default="atendente")


def agora_utc() -> datetime:
    return datetime.now(UTC)


class Evento(Base):
    """Uma linha da auditoria: quem fez o quê, e quando."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    quando: Mapped[datetime] = mapped_column(default=agora_utc)
    usuario: Mapped[str] = mapped_column(String(30))
    acao: Mapped[str] = mapped_column(String(40))
    detalhe: Mapped[str]


class MensagemAssistente(Base):
    """Uma fala de uma conversa com o assistente público, guardada no servidor."""

    __tablename__ = "mensagens_assistente"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversa: Mapped[str] = mapped_column(String(32), index=True)
    papel: Mapped[str] = mapped_column(String(10))
    texto: Mapped[str]
    quando: Mapped[datetime] = mapped_column(default=agora_utc)
    tokens_entrada: Mapped[int | None]
    tokens_saida: Mapped[int | None]
