# Controle de estoque com SQLite

Projeto pessoal em Python para praticar cadastro de produtos, movimentacoes de entrada e saida e consultas SQL locais.

O banco fica em um arquivo SQLite na maquina. O repositorio nao envia dados para servicos externos; o exemplo nao contem informacoes reais.

## Recursos

- Cadastra produtos com codigo unico e estoque minimo.
- Registra entradas e saidas com data e hora.
- Impede saida maior que o saldo disponivel.
- Lista saldo atual e sinaliza itens abaixo do minimo.
- Usa comandos SQL parametrizados e transacoes.

## Como executar

Requer Python 3.10 ou superior. Nao ha dependencias externas.

```bash
python controle_estoque.py --banco dados/estoque.db adicionar P001 "Caderno" 10 3
python controle_estoque.py --banco dados/estoque.db listar
python controle_estoque.py --banco dados/estoque.db entrada P001 5
python controle_estoque.py --banco dados/estoque.db saida P001 2
```

O banco e criado automaticamente quando um comando e executado.

## Estrutura

```text
controle_estoque.py   # interface de linha de comando e acesso ao SQLite
```

## Limites

Projeto de estudo. Nao substitui um sistema comercial, nao tem controle de usuarios e nao deve ser usado como registro oficial de estoque.
