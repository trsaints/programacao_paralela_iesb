# Versão OpenMP

Esta pasta receberá `04_convolucao_openmp.cpp`.

## Contrato com a automação

- Compilação: `make openmp`;
- Executável esperado: `openmp/convolucao_openmp.out`;
- Execução: `./openmp/convolucao_openmp.out N PASSES`;
- Threads: controladas por `OMP_NUM_THREADS`;
- Saída obrigatória: uma linha no formato
  `N=... passes=... checksum=... tempo=... s`.

O script `../script_medicao.py` valida o checksum contra o baseline e grava os
dados em `openmp/dados/`.
