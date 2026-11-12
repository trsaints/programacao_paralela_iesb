# Relatório Técnico de Baseline e Plano de Perfilamento

> **Status: versão revisada e reproduzível**
>
> Esta versão substitui `relatorio_teorico.v1.md` como referência para os
> resultados atuais do grupo. Os dados experimentais foram gerados por
> `script_medicao.py` e estão preservados em
> `baseline/dados/baseline_medicoes.csv` e
> `baseline/dados/baseline_resumo.csv`.

**Identificação do trio:** Thiago Rodrigues Santos, Andre Carvalho, Felipe Oliveira
**Problema escolhido:** Problema 4 — Filtro de convolução 2D (blur)

## 1. Descrição do Problema e Análise Algorítmica Sequencial

O problema aplica iterativamente um filtro de média (*blur*) 3×3 em uma imagem
sintética de dimensão `N × N`, por `P` passes. O código de referência fornecido
pelo professor está em `baseline/04_convolucao.cpp` e define o resultado correto
das futuras versões paralelas por meio do checksum final.

### 1.1 Estrutura de Dados e Mapeamento de Memória

A imagem é representada por dois vetores contíguos de `float`, `a` e `b`, cada
um com `N²` elementos. A conversão da coordenada bidimensional `(y, x)` para o
índice linear é:

\[
indice(y, x) = y \times N + x.
\]

Para cada pixel interno, com `1 ≤ y < N - 1` e `1 ≤ x < N - 1`, o programa
calcula:

\[
b[y,x] = \frac{1}{9}\sum_{dy=-1}^{1}\sum_{dx=-1}^{1}a[y+dy,x+dx].
\]

Ao fim de cada passe, `a.swap(b)` troca os buffers sem copiar a matriz. As bordas
não são recalculadas; esse comportamento, inclusive a alternância dos buffers,
deve ser preservado pelas versões OpenMP e MPI para manter o mesmo checksum.

### 1.2 Complexidade Assintótica

- **Tempo:** cada passe calcula `(N - 2)²` pixels internos, e cada cálculo usa
  uma vizinhança fixa de 9 elementos. Portanto,
  \(O(P \times (N-2)^2 \times 9) = O(PN^2)\).
- **Espaço:** há dois vetores de `N²` valores `float`, logo o consumo é
  \(O(N^2)\).

## 2. Análise Microarquitetural e Intensidade Computacional

Esta seção registra observações verificáveis diretamente no código; não foram
usados `perf`, PAPI, gprof ou um modelo Roofline nesta medição.

### 2.1 Padrões de Acesso à Memória

Os vetores são armazenados em ordem de linhas (*row-major*). Para cada valor de
`y`, o laço de `x` avança por endereços consecutivos, favorecendo localidade
espacial. Os acessos com `dy = -1, 0, 1` percorrem três linhas adjacentes; a
distância entre posições da mesma coluna em linhas consecutivas é `N` elementos.

### 2.2 Contagem Reproduzível do Trabalho do Stencil

Para cada pixel interno e cada passe, o código-fonte executa 9 leituras de `a`,
9 acumulações em `s`, uma divisão por `9.0f` e uma escrita em `b`. Assim, o
número de contribuições de vizinhança é exatamente:

\[
C_{viz}(N,P) = 9P(N-2)^2.
\]

Essa contagem identifica por que o stencil é o candidato natural à
paralelização, mas não é uma medição de FLOPs efetivos nem uma prova de limite
de banda de memória: o compilador e a hierarquia de cache podem alterar o custo
real por contribuição.

## 3. Perfilamento, Hotspots e Baseline Medido

### 3.1 Escopo da Instrumentação Fornecida

O baseline usa `clock_gettime(CLOCK_MONOTONIC)` antes do primeiro passe e depois
do último `a.swap(b)`. Portanto, o campo `tempo` mede os `P` passes de convolução
e as trocas de buffer; inicialização e checksum ficam fora desse intervalo.

| Trecho | Está no campo `tempo`? | Evidência disponível | Conclusão |
| --- | --- | --- | --- |
| Inicialização de `a` | Não | ocorre antes de `t0` | não é quantificada pelo baseline |
| Convolução 3×3 e `a.swap(b)` | Sim | intervalo `t0`–`t1` e CSVs | hotspot medido |
| Checksum | Não | ocorre após `t1` | não é quantificado pelo baseline |

Como o único trecho cronometrado pelo código de referência é o núcleo dos
passes, não são apresentados percentuais experimentais por subtrecho. O hotspot
é identificado pela medição desse núcleo e pela contagem `9P(N-2)^2`, muito
maior que os percursos lineares de inicialização e checksum para `P = 30`.

### 3.2 Resultados do Baseline

| N | Passes | Repetições | Checksum | Média (s) | Mediana (s) | Desvio-padrão (s) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 30 | 10 | 132592104.90 | 0.144690 | 0.142316 | 0.006689 |
| 2048 | 30 | 10 | 532566143.87 | 0.619539 | 0.613662 | 0.046888 |
| 4096 | 30 | 10 | 2134674862.94 | 2.694926 | 2.688303 | 0.144274 |

Os 30 tempos brutos e os resumos estatísticos estão, respectivamente, em
`baseline/dados/baseline_medicoes.csv` e
`baseline/dados/baseline_resumo.csv`. Para uma futura curva de speedup, a
mediana será usada como tempo de referência `T1`, pois é menos sensível a
variações ocasionais do sistema operacional.

## 4. Estimativa Teórica de Aceleração pela Lei de Amdahl

A Lei de Amdahl é dada por:

\[
S(q) = \frac{1}{(1-f) + \frac{f}{q}},
\]

em que `q` é o número de threads ou processos e `f` é a fração paralelizável.

### 4.1 Modelo Analítico Reproduzível para a Fração Paralelizável

Como o baseline não mede os subtrechos separadamente, `f` não é tratado como
resultado de profiler. Para produzir uma estimativa auditável, adotou-se um
modelo conservador de contagem de acessos lógicos: as 9 contribuições de cada
pixel do stencil são paralelizáveis; a inicialização e o checksum são dois
percursos lineares tratados como seriais. Assim:

\[
f(N,P) = \frac{9P(N-2)^2}{9P(N-2)^2 + 2N^2}.
\]

Para `P = 30`, a menor fração entre os três tamanhos testados ocorre em
`N = 1024`: `f = 0.992618`. Esse valor é uma estimativa teórica do algoritmo
completo; o tempo experimental `T1` continua sendo exclusivamente o intervalo
`t0`–`t1` do baseline.

### 4.2 Projeções de Speedup Teórico

Usando `f = 0.992618` de forma conservadora:

| Unidades de processamento (`q`) | Speedup previsto |
| ---: | ---: |
| 4 | 3.91× |
| 8 | 7.61× |
| Limite `q → ∞` | 135.47× |

Esses valores ignoram overhead de criação de threads, sincronização, comunicação
MPI e limite de banda de memória. As curvas medidas nas versões paralelas serão
comparadas a essa projeção no Marco 2.

## 5. Metodologia e Protocolo Experimental de Medição

O script `script_medicao.py` recompila o baseline com `g++ -O2`, executa o
aquecimento e produz os CSVs. Para cada tamanho, a primeira execução é
descartada e são registradas 10 repetições válidas.

| Item | Configuração |
| --- | --- |
| Tamanhos de entrada | `N = 1024`, `2048` e `4096` |
| Passes | `P = 30` |
| Aquecimento | 1 execução descartada por tamanho |
| Amostragem | 10 repetições por tamanho |
| Cronômetro | `clock_gettime(CLOCK_MONOTONIC)` no baseline |
| Estatísticas | média, mediana e desvio-padrão |
| Compilação | `g++ -O2` |

As medições desta versão foram executadas no notebook pessoal de Thiago, com
AMD Ryzen 7 5700U (8 núcleos físicos e 16 threads lógicas), 17 GB de RAM,
Fedora Linux 44, GCC 16.2.1 e Python 3.14.7. Antes da apresentação, o protocolo
deve ser repetido na máquina do laboratório, que é o ambiente de referência da
disciplina.

## 6. Plano Teórico de Paralelização

### 6.1 Estratégia OpenMP (Memória Compartilhada)

O laço externo de linhas (`y`) será paralelizado dentro de cada passe com
`#pragma omp parallel for schedule(static)`. A carga por linha é uniforme; por
isso, `static` é o ponto de partida. Cada thread lê somente `a` e grava células
distintas de `b`, logo não há condição de corrida no stencil e não são
necessários `critical`, `atomic` ou `reduction` nesse cálculo. A barreira
implícita ao fim do laço deve ocorrer antes de `a.swap(b)`.

### 6.2 Estratégia MPI (Memória Distribuída)

O domínio será dividido em faixas horizontais. `MPI_Scatterv` distribuirá as
linhas iniciais e `MPI_Gatherv` reunirá a saída, inclusive quando `N` não for
divisível pelo número de processos. Antes de cada passe, processos vizinhos
trocarão uma linha de halo superior e inferior com `MPI_Sendrecv` ou operações
não bloqueantes. As bordas globais e a alternância dos dois buffers devem ser
preservadas. Após o `MPI_Gatherv`, o processo 0 calculará o checksum na mesma
ordem sequencial do baseline para uma comparação direta e reprodutível.
