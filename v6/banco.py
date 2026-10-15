# banco.py — conexão com o banco de dados

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import URL_BANCO

engine = create_engine(URL_BANCO)
SessaoLocal = sessionmaker(bind=engine)


if engine.dialect.name == "sqlite":
    # Só o SQLite precisa disto: ele vem com as chaves estrangeiras desligadas.
    @event.listens_for(engine, "connect")
    def liga_chaves_estrangeiras(conexao, registro) -> None:
        conexao.execute("PRAGMA foreign_keys = ON")


class Base(DeclarativeBase):
    pass


def cria_tabelas() -> None:
    import modelos  # noqa: F401  (o import registra as tabelas na Base)

    Base.metadata.create_all(engine)
