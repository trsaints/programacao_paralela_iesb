# Versão MPI — responsável: @andre

```sh
make mpi
mpirun -np 4 ./mpi/convolucao_mpi.out 1024 30 --validate
```

O domínio N×N é dividido em faixas horizontais contíguas. Os primeiros
N % processos ranks recebem uma linha adicional. MPI_Scatterv distribui
os pixels e MPI_Gatherv reconstrói a imagem no rank 0. Antes de cada passe,
dois MPI_Sendrecv trocam as linhas extremas com os vizinhos. Há uma linha
de halo acima e outra abaixo de cada faixa. Ranks sem linhas participam das
coletivas, mas não trocam halos. As bordas externas usam MPI_PROC_NULL.

Os dois buffers mantêm suas próprias bordas, exatamente como o baseline:
as bordas são zero nos passes ímpares e os valores iniciais nos pares.
A ordem das nove somas em float e a divisão são preservadas. Não compile
com -ffast-math, pois reassociar operações quebra essa garantia.

Somente o rank 0 imprime em stdout a linha compatível com script_medicao.py:
`N=... passes=... checksum=... tempo=... s`.
Em stderr, imprime `comunicacao_s=... computacao_s=...`.
`--validate` executa a referência sequencial no mestre e compara todos os
bytes dos pixels da imagem reconstruída; divergência retorna código 2.
A validação fica fora do intervalo cronometrado. Sem essa opção, o script
geral continua funcionando com sua comparação de checksum.

## Validação, campanha padronizada e gráficos

No ambiente Linux/contêiner do projeto, com OpenMPI, make, g++ e Python 3:

```sh
# Casos pequenos: bordas, paridade, faixas desiguais e ranks vazios
python3 mpi/script_analise.py --test --processos 1 2 4

# Campanha oficial do seminário: baseline e versões disponíveis
python3 script_medicao.py

# Gerar gráficos a partir dos CSVs dessa campanha, sem medir novamente
python3 mpi/script_analise.py

# Verificações Python sem MPI
python3 -m unittest discover -s mpi -p 'test_*.py'
```

`script_medicao.py` é a única campanha de medição. Segue os tamanhos,
repetições e colunas definidos no README do seminário e limita as unidades
às CPUs disponíveis. Antes de medir, verifica também os slots reais do OpenMPI;
configurações sem slots suficientes são informadas como `SKIPPED`, sem
ativar oversubscription. A contagem de CPUs lógicas pode ser maior que a
quantidade de slots, pois o OpenMPI usa núcleos físicos por padrão.
Valida todos os pixels em cada execução MPI (fora do
tempo medido) e compara o checksum com o executável baseline original.
Gera `mpi/dados/mpi_medicoes.csv`, `mpi/dados/mpi_resumo.csv` e as métricas
compartilhadas em `dados/metricas.csv`, além dos CSVs do baseline e OpenMP
quando disponível. A campanha sobrescreve os dados anteriores desses arquivos.

Os tempos de comunicação e computação são um complemento em
`mpi/dados/mpi_overhead.csv`, com as mesmas chaves de configuração e repetição
das medições MPI; as colunas dos arquivos padronizados permanecem intactas.
O gerador lê `dados/metricas.csv` para speedup/eficiência e `mpi_overhead.csv`
para as componentes. Salva quatro SVGs em `mpi/graficos/` sem dependências
externas. Ele não executa uma segunda campanha.

Os arquivos antigos `analise_*.csv` são históricos da campanha anterior,
não são mais produzidos nem consumidos. Gere novamente a campanha padrão
antes de atualizar os gráficos; não combine baselines de campanhas diferentes.
Se a campanha falhar, o gerador bloqueia a atualização dos gráficos até uma
nova execução terminar com sucesso. Para encadear os comandos, use
`python3 script_medicao.py && python3 mpi/script_analise.py`.

Speedup = mediana do tempo baseline / mediana do tempo MPI;
eficiência = speedup / número de processos. O tempo MPI inclui distribuição,
halos e reunião; exclui inicialização da imagem, validação, checksum e
reduções de instrumentação. Uma barreira precede a medição. Comunicação
mede o tempo dentro de Scatterv, Sendrecv e Gatherv, incluindo espera;
computação mede os laços locais e a troca dos buffers. Cada tempo reportado
é o máximo entre ranks (MPI_Reduce), portanto os máximos das componentes
podem vir de ranks diferentes e não devem ser somados como decomposição
exata do tempo total. O total inclui também o controle dos passes.

Execute a campanha no hardware da disciplina para produzir as curvas finais.
Use no máximo o número de slots disponíveis no OpenMPI ou configure
explicitamente oversubscription para testes funcionais; não use
oversubscription para comparar desempenho.
