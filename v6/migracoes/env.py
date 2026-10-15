# migracoes/env.py — como o Alembic encontra o banco e os modelos

from logging.config import fileConfig

from alembic import context

import modelos  # noqa: F401  (o import registra as tabelas na Base)
from banco import Base, engine

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)  # mostra o que o Alembic está fazendo
target_metadata = Base.metadata


def roda_migracoes() -> None:
    with engine.connect() as conexao:
        # Para alterar uma tabela, o SQLite copia, apaga e recria a tabela.
        # Com as chaves estrangeiras ligadas, apagar "clientes" seria recusado
        # (há aluguéis apontando para ela). Durante a migração, desligamos.
        if conexao.dialect.name == "sqlite":
            conexao.exec_driver_sql("PRAGMA foreign_keys = OFF")
            conexao.commit()
        context.configure(
            connection=conexao,
            target_metadata=target_metadata,
            render_as_batch=True,  # necessário para alterar tabelas no SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


roda_migracoes()
