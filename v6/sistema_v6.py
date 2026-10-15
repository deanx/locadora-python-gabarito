# sistema_v6.py — a locadora rodando sobre o banco de dados

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from banco import SessaoLocal
from historico import mostra_historico
from modelos import Aluguel, Cliente, Veiculo
from moeda import formata_brl
from relatorios import (
    exporta_frota_csv,
    faturamento_por_cliente,
    frota_por_tipo,
    veiculos_mais_alugados,
)
from servicos import NaoEncontrado, OperacaoInvalida, finaliza_aluguel, registra_aluguel


def menu() -> None:
    print()
    print("=== LOCADORA v6 (banco de dados) ===")
    print("  [1] Listar frota        [2] Listar clientes")
    print("  [3] Cadastrar cliente   [4] Registrar aluguel")
    print("  [5] Finalizar aluguel   [6] Aluguéis em andamento")
    print("  [9] Exportar frota (CSV)")
    print("  [0] Sair")


def main() -> None:
    with SessaoLocal() as sessao:
        while True:
            menu()
            opcao = input("Opção: ").strip()
            try:
                match opcao:
                    case "1":
                        for v in sessao.scalars(select(Veiculo).order_by(Veiculo.placa)):
                            print(" ", v)
                    case "2":
                        for c in sessao.scalars(select(Cliente).order_by(Cliente.nome)):
                            print(" ", c)
                    case "3":
                        nome = input("Nome: ").strip()
                        cpf = input("CPF (só números): ").strip()
                        idade = int(input("Idade: "))
                        sessao.add(Cliente(nome=nome, cpf=cpf, idade=idade))
                        sessao.commit()
                        print(f"Cliente {nome} cadastrado.")
                    case "4":
                        cpf = input("CPF do cliente: ").strip()
                        placa = input("Placa: ").strip()
                        dias = int(input("Dias: "))
                        aluguel = registra_aluguel(sessao, cpf, placa, dias)
                        print(
                            f"Aluguel #{aluguel.id} registrado: {formata_brl(aluguel.valor_final)}"
                        )
                    case "5":
                        aluguel_id = int(input("Número do aluguel: "))
                        aluguel = finaliza_aluguel(sessao, aluguel_id)
                        print(
                            f"Aluguel #{aluguel.id} finalizado. {aluguel.veiculo.placa} devolvido."
                        )
                    case "6":
                        consulta = select(Aluguel).where(Aluguel.finalizado == False)
                        for a in sessao.scalars(consulta):
                            print(" ", a)
                    case "7":
                        print("--- Frota por tipo ---")
                        for grupo in frota_por_tipo(sessao):
                            print(
                                f"  {grupo.tipo}: {grupo.total} ({grupo.disponiveis} disponíveis)"
                            )
                        print("--- Faturamento por cliente ---")
                        for fatura in faturamento_por_cliente(sessao):
                            print(f"  {fatura.cliente}: {formata_brl(fatura.total)}")
                        print("--- Mais alugados ---")
                        for campeao in veiculos_mais_alugados(sessao):
                            print(f"  {campeao.placa} {campeao.modelo}: {campeao.vezes}x")
                    case "8":
                        cpf = input("CPF: ").strip()
                        mostra_historico(sessao, cpf)
                    case "9":
                        caminho = exporta_frota_csv(sessao, Path("exportacoes"))
                        print(f"Frota exportada para {caminho}")
                    case "0":
                        print("Até logo!")
                        break
                    case _:
                        print(f"Opção '{opcao}' inválida.")
            except (NaoEncontrado, OperacaoInvalida) as erro:
                print(f"Não foi possível: {erro}")
            except IntegrityError:
                sessao.rollback()
                print("Já existe um cadastro com esse CPF.")
            except ValueError:
                print("Valor inválido — digite um número.")


if __name__ == "__main__":
    main()
