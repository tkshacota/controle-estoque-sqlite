"""Controle local de produtos e movimentacoes usando SQLite."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def conectar(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.executescript(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            codigo TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK (quantidade >= 0),
            estoque_minimo INTEGER NOT NULL CHECK (estoque_minimo >= 0)
        );
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY,
            codigo_produto TEXT NOT NULL REFERENCES produtos(codigo),
            tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
            quantidade INTEGER NOT NULL CHECK (quantidade > 0),
            registrado_em TEXT NOT NULL
        );
        """
    )
    return conexao


def adicionar(conexao: sqlite3.Connection, codigo: str, nome: str, quantidade: int, minimo: int) -> None:
    if not codigo.strip() or not nome.strip():
        raise ValueError("codigo e nome do produto sao obrigatorios")
    if quantidade < 0 or minimo < 0:
        raise ValueError("quantidade e estoque minimo nao podem ser negativos")
    conexao.execute(
        "INSERT INTO produtos (codigo, nome, quantidade, estoque_minimo) VALUES (?, ?, ?, ?)",
        (codigo.strip(), nome.strip(), quantidade, minimo),
    )
    if quantidade:
        registrar_movimentacao(conexao, codigo, "entrada", quantidade)
    conexao.commit()


def registrar_movimentacao(
    conexao: sqlite3.Connection, codigo: str, tipo: str, quantidade: int
) -> None:
    if quantidade <= 0:
        raise ValueError("a quantidade da movimentacao deve ser maior que zero")

    produto = conexao.execute(
        "SELECT quantidade FROM produtos WHERE codigo = ?", (codigo.strip(),)
    ).fetchone()
    if produto is None:
        raise ValueError(f"produto nao encontrado: {codigo}")

    saldo_atual = int(produto[0])
    if tipo == "saida" and quantidade > saldo_atual:
        raise ValueError("a saida excede o saldo disponivel")

    variacao = quantidade if tipo == "entrada" else -quantidade
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conexao:
        conexao.execute(
            "UPDATE produtos SET quantidade = quantidade + ? WHERE codigo = ?",
            (variacao, codigo.strip()),
        )
        conexao.execute(
            "INSERT INTO movimentacoes "
            "(codigo_produto, tipo, quantidade, registrado_em) VALUES (?, ?, ?, ?)",
            (codigo.strip(), tipo, quantidade, agora),
        )


def listar(conexao: sqlite3.Connection) -> list[tuple[str, str, int, int]]:
    return conexao.execute(
        "SELECT codigo, nome, quantidade, estoque_minimo "
        "FROM produtos ORDER BY nome COLLATE NOCASE, codigo"
    ).fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", type=Path, default=Path("dados/estoque.db"))
    comandos = parser.add_subparsers(dest="comando", required=True)

    cadastro = comandos.add_parser("adicionar", help="cadastra um produto")
    cadastro.add_argument("codigo")
    cadastro.add_argument("nome")
    cadastro.add_argument("quantidade", type=int)
    cadastro.add_argument("estoque_minimo", type=int)

    entrada = comandos.add_parser("entrada", help="registra entrada de unidades")
    entrada.add_argument("codigo")
    entrada.add_argument("quantidade", type=int)

    saida = comandos.add_parser("saida", help="registra saida de unidades")
    saida.add_argument("codigo")
    saida.add_argument("quantidade", type=int)

    comandos.add_parser("listar", help="lista os produtos e seus saldos")
    argumentos = parser.parse_args()

    try:
        with conectar(argumentos.banco) as conexao:
            if argumentos.comando == "adicionar":
                adicionar(
                    conexao,
                    argumentos.codigo,
                    argumentos.nome,
                    argumentos.quantidade,
                    argumentos.estoque_minimo,
                )
                print(f"Produto {argumentos.codigo} cadastrado.")
            elif argumentos.comando in {"entrada", "saida"}:
                registrar_movimentacao(
                    conexao, argumentos.codigo, argumentos.comando, argumentos.quantidade
                )
                print(f"Movimentacao de {argumentos.comando} registrada.")
            else:
                for codigo, nome, quantidade, minimo in listar(conexao):
                    alerta = " - abaixo do minimo" if quantidade < minimo else ""
                    print(f"{codigo} | {nome} | saldo: {quantidade} | minimo: {minimo}{alerta}")
    except (OSError, sqlite3.Error, ValueError) as erro:
        parser.error(str(erro))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
