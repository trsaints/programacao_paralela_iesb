# Projeto de Seminário

O projeto encontra-se no diretório `seminario/`.
Para executá-lo, realize as seguintes etapas em seu terminal:
```sh
cd seminario
python3 script_medicao.py
```

Para apenas conferir quais versões estão disponíveis sem compilar ou medir:

```sh
python3 script_medicao.py --dry-run
```

## Medições

O script sempre exige e mede o baseline. Enquanto ainda não existirem, as
versões OpenMP e MPI são registradas como `SKIPPED` em vez de interromper a
campanha. Quando implementadas, o script espera estes arquivos:

```text
openmp/04_convolucao_openmp.cpp
mpi/04_convolucao_mpi.cpp
```

As três versões devem aceitar `N` e `passes` como argumentos e emitir uma linha
no formato:

```text
N=... passes=... checksum=... tempo=... s
```

Os resultados da campanha são gravados em `dados/medicoes.csv`,
`dados/resumo.csv`, `dados/metricas.csv` e `dados/execucoes_ignoradas.csv`.
Os arquivos `baseline_medicoes.csv` e `baseline_resumo.csv` continuam sendo
gerados para manter compatibilidade com o relatório técnico.

## Ambiente experimental

Máquina: notebook pessoal (thiago)
- CPU: AMD Ryzen 7 5700U with Radeon Graphics
- Núcleos físicos: 8
- Threads lógicas: 16
- Memória RAM: 17GB
- Sistema operacional: Fedora Linux 44 (Workstation Edition)
- Compilador: g++ (GCC) 16.2.1 20261029 (Red Hat 16.2.1-3)
- Flags de compilação: `-O2`
- Python: 3.14.7
