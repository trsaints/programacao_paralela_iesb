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

## Comparativo de desempenho da convolução 2D

Os testes de escalabilidade forte usam 30 passadas e a mediana de duas
execuções por configuração. O speedup é o tempo mediano do baseline
sequencial dividido pelo tempo mediano da configuração para a mesma matriz.
A eficiência é o speedup dividido pelo número de threads ou processos,
expresso em porcentagem.

| Matriz | Unidades | Baseline (s) | OpenMP (s) | OpenMP speedup | OpenMP eficiência | MPI (s) | MPI speedup | MPI eficiência |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 × 1024 | 1 | 0,117338 | 0,116086 | 1,01× | 101,1% | 0,112357 | 1,04× | 104,4% |
| 1024 × 1024 | 2 | 0,117338 | 0,065833 | 1,78× | 89,1% | 0,058802 | 2,00× | 99,8% |
| 1024 × 1024 | 4 | 0,117338 | 0,031470 | 3,73× | 93,2% | 0,044396 | 2,64× | 66,1% |
| 1024 × 1024 | 8 | 0,117338 | 0,019186 | 6,12× | 76,4% | 0,031741 | 3,70× | 46,2% |
| 2048 × 2048 | 1 | 0,440322 | 0,447574 | 0,98× | 98,4% | 0,443025 | 0,99× | 99,4% |
| 2048 × 2048 | 2 | 0,440322 | 0,230327 | 1,91× | 95,6% | 0,246712 | 1,78× | 89,2% |
| 2048 × 2048 | 4 | 0,440322 | 0,130775 | 3,37× | 84,2% | 0,145310 | 3,03× | 75,8% |
| 2048 × 2048 | 8 | 0,440322 | 0,090849 | 4,85× | 60,6% | 0,120726 | 3,65× | 45,6% |
| 4096 × 4096 | 1 | 1,835957 | 1,917418 | 0,96× | 95,8% | 1,802190 | 1,02× | 101,9% |
| 4096 × 4096 | 2 | 1,835957 | 0,966948 | 1,90× | 94,9% | 0,921143 | 1,99× | 99,7% |
| 4096 × 4096 | 4 | 1,835957 | 0,549325 | 3,34× | 83,6% | 0,532609 | 3,45× | 86,2% |
| 4096 × 4096 | 8 | 1,835957 | 0,385605 | 4,76× | 59,5% | 0,575562 | 3,19× | 39,9% |

O baseline usa uma unidade e tem speedup de 1,00× e eficiência de 100% por
definição. O tempo do MPI inclui a distribuição inicial e a coleta final da
matriz. [Dados completos das medições](seminario/dados/forte/metricas.csv).

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
    ├── HARDWARE.md
    ├── script_medicao.py
    ├── baseline/
    ├── openmp/
    ├── mpi/
    ├── dados/
    └── graficos/
```
