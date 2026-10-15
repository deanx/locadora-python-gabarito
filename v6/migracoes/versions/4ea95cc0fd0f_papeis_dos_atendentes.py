"""papeis dos atendentes

Revision ID: 4ea95cc0fd0f
Revises: a54d02b91576
Create Date: 2026-10-06 22:45:07.800893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ea95cc0fd0f'
down_revision: Union[str, Sequence[str], None] = 'a54d02b91576'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Troca o gerente (sim/não) por um papel, preservando quem já é gerente."""
    # 1. A coluna nova, com um padrão para as linhas que já existem
    with op.batch_alter_table("atendentes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("papel", sa.String(length=20), nullable=False, server_default="atendente")
        )

    # 2. O dado: quem era gerente continua gerente
    op.execute("UPDATE atendentes SET papel = 'gerente' WHERE gerente")

    # 3. Só agora a coluna antiga pode sair
    with op.batch_alter_table("atendentes", schema=None) as batch_op:
        batch_op.drop_column("gerente")


def downgrade() -> None:
    """O caminho de volta: o auditor vira atendente comum (não existia antes)."""
    with op.batch_alter_table("atendentes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("gerente", sa.Boolean(), nullable=False, server_default=sa.false())
        )

    op.execute("UPDATE atendentes SET gerente = TRUE WHERE papel = 'gerente'")

    with op.batch_alter_table("atendentes", schema=None) as batch_op:
        batch_op.drop_column("papel")
