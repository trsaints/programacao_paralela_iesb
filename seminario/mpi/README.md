# Versão MPI

Esta pasta receberá `04_convolucao_mpi.cpp`.

## Contrato com a automação

- Compilação: `make mpi`;
- Executável esperado: `mpi/convolucao_mpi.out`;
- Execução local: `mpirun -np P ./mpi/convolucao_mpi.out N PASSES`;
- Apenas o rank 0 deve imprimir uma linha no formato
  `N=... passes=... checksum=... tempo=... s`.

O script `../script_medicao.py` valida o checksum contra o baseline e grava os
dados em `mpi/dados/`.
