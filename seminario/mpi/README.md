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

## Validação e campanha de overhead

No ambiente Linux/contêiner do projeto, com OpenMPI, make, g++ e Python 3:

```sh
# Casos pequenos: bordas, paridade, faixas desiguais e ranks vazios
python3 mpi/script_analise.py --test --processos 1 2 4

# Campanha completa: 1 aquecimento, 10 repetições, 30 passes
python3 mpi/script_analise.py

# Campanha curta
python3 mpi/script_analise.py --tamanhos 32 65 --passes 3 --processos 1 2 4 --repeticoes 2

# Verificações Python sem MPI
python3 -m unittest discover -s mpi -p 'test_*.py'
```

A campanha compila os programas, valida todos os pixels em cada execução MPI
e compara o checksum com o executável baseline original. Gera
mpi/dados/analise_medicoes.csv (amostras MPI e baseline),
mpi/dados/analise_resumo.csv (medianas), e quatro gráficos SVG em
mpi/graficos/: speedup, eficiência, comunicação e computação. Usa apenas
a biblioteca padrão Python. Preserva os dados da campanha geral.

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
