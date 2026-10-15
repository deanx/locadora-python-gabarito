"""nome de busca do cliente

Revision ID: 7544587a7ba4
Revises: dabc59224e32
Create Date: 2026-10-08 06:10:31.781315

"""
from typing import Sequence, Union

from alembic import op
import unicodedata

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7544587a7ba4'
down_revision: Union[str, Sequence[str], None] = 'dabc59224e32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _chave_busca(texto: str) -> str:
    # Cópia da texto.chave_busca, congelada como era quando esta migração foi
    # escrita: se a função do sistema mudar um dia, esta migração não muda junto.
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").casefold()


def upgrade() -> None:
    # 1. A coluna nasce aceitando nulo: os clientes que já existem não têm valor.
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("nome_busca", sa.String(), nullable=True))

    # 2. Preenche os clientes que já existem.
    conexao = op.get_bind()
    clientes = conexao.execute(sa.text("SELECT id, nome FROM clientes")).all()
    for id_, nome in clientes:
        conexao.execute(
            sa.text("UPDATE clientes SET nome_busca = :chave WHERE id = :id"),
            {"chave": _chave_busca(nome), "id": id_},
        )

    # 3. Agora, todos têm valor: a coluna passa a ser obrigatória, e ganha o índice.
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.alter_column("nome_busca", existing_type=sa.String(), nullable=False)
        batch_op.create_index(batch_op.f("ix_clientes_nome_busca"), ["nome_busca"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_clientes_nome_busca"))
        batch_op.drop_column("nome_busca")
