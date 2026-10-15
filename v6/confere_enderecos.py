# confere_enderecos.py — confere, em lote, o endereço dos clientes com CEP (caderno 15)

import asyncio
from dataclasses import dataclass, field

from sqlalchemy import select

import enderecos
from banco import SessaoLocal
from enderecos import CepInvalido, CepNaoEncontrado, Endereco, ServicoCepIndisponivel
from modelos import Cliente

LIMITE_SIMULTANEO = 5  # respeita o serviço de CEP: no máximo 5 consultas ao mesmo tempo

FALHAS_ESPERADAS = (CepInvalido, CepNaoEncontrado, ServicoCepIndisponivel)


@dataclass
class Conferencia:
    encontrados: dict[str, Endereco] = field(default_factory=dict)
    falhas: dict[str, str] = field(default_factory=dict)


async def _confere_um(cep: str, limite: asyncio.Semaphore, resultado: Conferencia) -> None:
    async with limite:
        try:
            resultado.encontrados[cep] = await enderecos.busca_endereco(cep)
        except FALHAS_ESPERADAS as erro:
            # Uma falha esperada fica no relatório e NÃO cancela as outras consultas.
            # Um erro inesperado sobe, e o TaskGroup cancela o lote inteiro.
            resultado.falhas[cep] = type(erro).__name__


async def confere_ceps(ceps: list[str], limite_simultaneo: int = LIMITE_SIMULTANEO) -> Conferencia:
    resultado = Conferencia()
    limite = asyncio.Semaphore(limite_simultaneo)
    async with asyncio.TaskGroup() as grupo:
        for cep in dict.fromkeys(ceps):  # cada CEP uma vez só, mesmo que se repita
            grupo.create_task(_confere_um(cep, limite, resultado), name=f"cep-{cep}")
    return resultado


def divergencias(clientes: list[Cliente], conferencia: Conferencia) -> list[str]:
    linhas = []
    for cliente in clientes:
        if cliente.cep is None:
            continue
        if cliente.cep in conferencia.falhas:
            linhas.append(f"{cliente.nome}: não conferido ({conferencia.falhas[cliente.cep]})")
            continue
        novo = conferencia.encontrados[cliente.cep]
        if (cliente.logradouro, cliente.cidade, cliente.uf) != (
            novo.logradouro,
            novo.cidade,
            novo.uf,
        ):
            linhas.append(
                f"{cliente.nome}: cadastro diz {cliente.cidade}/{cliente.uf}, o CEP diz {novo.cidade}/{novo.uf}"
            )
    return linhas


def main() -> None:
    with SessaoLocal() as sessao:
        clientes = list(sessao.scalars(select(Cliente).where(Cliente.cep.is_not(None))))
    conferencia = asyncio.run(confere_ceps([c.cep for c in clientes if c.cep]))
    print(f"{len(clientes)} clientes com CEP; {len(conferencia.falhas)} CEPs sem resposta")
    for linha in divergencias(clientes, conferencia):
        print(" -", linha)


if __name__ == "__main__":
    main()
