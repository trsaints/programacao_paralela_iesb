# Programação Paralela — IESB 2026/2

Repositório de atividades da disciplina de Programação Paralela, turma 2026/2
(noturno).

## Projeto acadêmico

O artefato do Projeto Acadêmico de convolução 2D está isolado em
[`seminario/`](seminario/). Esse diretório possui seu próprio `Makefile`,
ambiente Docker/Dev Container, automação de medições e documentação de entrega.

Para compilar ou verificar o projeto acadêmico:

```sh
cd seminario
make baseline
python3 script_medicao.py --dry-run
```

Consulte [`seminario/README.md`](seminario/README.md) para executar o projeto
do zero no laboratório ou no contêiner oficial. Os demais diretórios são
atividades independentes e não fazem parte do artefato de convolução 2D.

## Dev Container e versionamento

Abra a **raiz deste repositório** no VS Code e escolha **Dev Containers: Reopen
in Container**. A configuração em `.devcontainer/` usa a montagem explícita de
`docker-compose.yml` para disponibilizar o repositório inteiro em `/workspace`,
portanto o explorador, o controle de versão e o terminal continuam vendo todos
os arquivos Git. O contêiner inclui `git` somente para viabilizar esse controle
de versão e já confia na montagem `/workspace`; não é necessário clonar outro
repositório. Compilação e medições usam o mesmo conjunto de ferramentas CCO085.

Dentro do contêiner, entre em `seminario/` para compilar ou medir o projeto:

```sh
cd seminario
make baseline
```

## Estrutura do repositório

```text
programacao_paralela_iesb/
├── README.md
├── .gitignore
├── .devcontainer/
├── .vscode/
├── desafios/
│   └── coeficiente_variacao/
└── seminario/
    ├── Makefile
    ├── README.md
    ├── Dockerfile
    ├── docker-compose.yml
    ├── script_medicao.py
    ├── baseline/
    ├── openmp/
    ├── mpi/
    ├── dados/
    └── graficos/
```
