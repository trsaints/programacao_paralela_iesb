# Dados da versão MPI

`script_medicao.py` criará nesta pasta:

- `mpi_medicoes.csv`: tempos brutos por processo e repetição;
- `mpi_resumo.csv`: média, mediana e desvio-padrão por configuração.
- `mpi_overhead.csv`: complemento com as mesmas chaves das medições MPI e
  tempos separados de comunicação e computação; não altera as colunas dos
  dois arquivos padronizados.

Speedup e eficiência ficam em `../../dados/metricas.csv`. Execute
`python3 mpi/script_analise.py` a partir de `seminario/` para gerar os SVGs
usando esses CSVs. Os arquivos `analise_*.csv` são históricos e não são usados
pelo fluxo padronizado.

Os dados só devem ser usados em gráficos finais após a validação do checksum e
a execução da campanha no ambiente oficial.
