# Dados da versão MPI

`script_medicao.py` cria os diretórios `forte/` e `fraca/` nesta pasta. Cada
um contém:

- `mpi_medicoes.csv`: tempos brutos por processo e repetição;
- `mpi_resumo.csv`: média, mediana e desvio-padrão por configuração.
- `mpi_overhead.csv`: complemento com as mesmas chaves das medições MPI e
  tempos separados de comunicação e computação; não altera as colunas dos
  dois arquivos padronizados.

Speedup e eficiência ficam em `../../dados/forte/metricas.csv`; tempo relativo
e eficiência fraca ficam em `../../dados/fraca/metricas.csv`. Execute
`python3 script_analise.py --campanha forte` ou
`python3 script_analise.py --campanha fraca` a partir de `seminario/` para
gerar os SVGs correspondentes.

Os dados só devem ser usados em gráficos finais após a validação do checksum e
a execução da campanha no ambiente oficial.
