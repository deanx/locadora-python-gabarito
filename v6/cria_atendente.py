# cria_atendente.py — cadastra um atendente que pode fazer login na API

import os
from getpass import getpass

from sqlalchemy import select

from banco import SessaoLocal
from modelos import Atendente
from papeis import Papel
from seguranca import gera_hash


def cria(usuario: str, nome: str, senha: str, papel: str = "atendente") -> None:
    with SessaoLocal() as sessao:
        existe = sessao.scalar(select(Atendente).where(Atendente.usuario == usuario))
        if existe is not None:
            print(f"Atendente {usuario} já existe. Nada a fazer.")
            return
        sessao.add(Atendente(usuario=usuario, nome=nome, senha_hash=gera_hash(senha), papel=papel))
        sessao.commit()
        print(f"Atendente {usuario} criado.")


if __name__ == "__main__":
    usuario = os.getenv("LOCADORA_ATENDENTE_USUARIO") or input("Usuário: ").strip()
    nome = os.getenv("LOCADORA_ATENDENTE_NOME") or input("Nome: ").strip()
    senha = os.getenv("LOCADORA_ATENDENTE_SENHA") or getpass("Senha: ")
    papel = os.getenv("LOCADORA_ATENDENTE_PAPEL") or input("Papel (atendente/gerente/auditor): ")
    cria(usuario, nome, senha, papel=Papel(papel.strip().lower()))
