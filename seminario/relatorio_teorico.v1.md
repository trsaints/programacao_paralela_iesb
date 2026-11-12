# **Relatório Técnico de Baseline e Plano de Perfilamento**

> **Status: documento histórico — supersedido**
>
> Este arquivo preserva o conteúdo do relatório originalmente entregue no
> Marco 1. As medições, o ambiente experimental e as estimativas registrados
> nesta versão foram produzidos por um ex-integrante do grupo em sua máquina
> pessoal. Após sua saída, o grupo atual não pôde reproduzir ou validar
> integralmente todos os dados e ferramentas citados neste documento.
>
> Portanto, este relatório deve ser tratado apenas como registro histórico e
> não como fonte dos resultados experimentais atuais. A versão revisada,
> baseada em medições reproduzíveis e nos artefatos atualmente mantidos pelo
> grupo, está em
> [`relatorio_teorico.v2.md`](relatorio_teorico.v2.md).

## **1\. Descrição do Problema e Análise Algorítmica Sequencial**

O problema consiste na aplicação iterativa de um filtro de convolução bidimensional do tipo média (blur) com kernel 3x3 sobre uma imagem sintética de dimensões N x N pixels ao longo de P passes temporais. O algoritmo original de referência foi fornecido em C++ (04\_convolucao.cpp) e serve como padrão absoluto de corretude (gabarito) para validação via checksum das futuras versões paralelas.

### **1.1 Estrutura de Dados e Mapeamento de Memória**

A imagem é armazenada em memória contígua utilizando vetores dinâmicos unidimensionais std::vector\<float\> de tamanho N² (estruturas A e B). A conversão de coordenadas bidimensionais (y, x) para a indexação linear é dada pela equação:

*Índice Linear \= y \* N \+ x*

Para cada pixel interno (y, x) com y ∈ \[1, N-2\] e x ∈ \[1, N-2\], calcula-se a média aritmética simples dos 9 pixels vizinhos contidos no quadrado 3x3 centrado em (y, x):

*B\[y, x\] \= (1 / 9.0) \* ∑dy=-11 ∑dx=-11 A\[y \+ dy, x \+ dx\]*

Ao término de cada passe p ∈ \[0, P-1\], executa-se a troca de ponteiros/buffers via a.swap(b), fazendo com que o resultado recém-calculado em B passe a ser a entrada para o próximo passo de suavização temporal.

### **1.2 Complexidade Assintótica**

* **Complexidade de Tempo:** O(P \* N²). Para um filtro 3x3 fixo (K=3), a cada passe são processados exatamente (N-2)² pixels internos, exigindo 9 acessos lógicos aos valores da vizinhança e 9 operações de ponto flutuante (8 somas e 1 multiplicação por escalar) por pixel. O custo computacional cresce de forma estritamente quadrática em relação ao lado da imagem N e linear em relação ao número de passes P.  
* **Complexidade de Espaço:** O(N²). São mantidos dois vetores completos de N² floats para evitar dependência de dados entre a leitura dos vizinhos e a escrita do pixel atual no mesmo buffer (técnica de duplo buffer).

## **2\. Análise Microarquitetural e Intensidade Computacional**

Uma análise detalhada da interação entre a estrutura do código e o hardware da CPU revela hipóteses estruturais para a caracterização do desempenho do baseline.

### **2.1 Padrões de Acesso à Cache (Locality Analysis)**

* **Localidade Espacial (Eixo X):** Os acessos na varredura da dimensão horizontal (dx \= \-1, 0, 1\) ocorrem em endereços contíguos de memória. Isso resulta em um aproveitamento ideal da linha de cache L1 (geralmente de 64 bytes, capaz de acomodar 16 valores do tipo float de 32 bits).  
* **Localidade Temporal e Stride (Eixo Y):** Os acessos na dimensão vertical (dy \= \-1, 0, 1\) realizam saltos (strides) de N \* sizeof(float) bytes na memória. Conforme N cresce, o deslocamento entre linhas aumenta a probabilidade de falhas de cache (cache misses) em matrizes maiores, hipótese que será validada experimentalmente com amostragem de eventos de hardware via contadores de desempenho (perf/PAPI).

### **2.2 Intensidade Computacional e Modelo Roofline**

A Intensidade Computacional (I) serve como métrica analítica preliminar para estimar a dependência da aplicação em relação ao processamento versus tráfego de memória:

* **Operações de Ponto Flutuante (FLOPs):** 8 somas \+ 1 multiplicação por escalar (1/9.0f) \= 9 FLOPs por pixel.  
* **Tráfego de Dados na Memória (Bytes):** 9 leituras de float (36 bytes) \+ 1 escrita de float (4 bytes) \= 40 bytes por pixel (no pior cenário sem reutilização em cache).

*Intensidade Computacional (I) \= 9 FLOPs / 40 Bytes \= 0,225 FLOPs/Byte*

**Análise Teórica do Baseline:** O valor I \= 0,225 FLOPs/Byte sugere um forte indicativo de comportamento **Memory-Bound**. No entanto, essa taxa isolada é um indicador teórico; a confirmação definitiva do gargalo em largura de banda dependerá do confronto com os limites de hardware da máquina de testes no Modelo Roofline e das medições do profiler.

## **3\. Estimativa de Hotspots e Plano de Perfilamento**

Para estruturar o plano de perfilamento e paralelização antes da instrumentação final, o algoritmo foi decomposto funcionalmente em três fases com estimativas analíticas baseadas na contagem de operações.

### **3.1 Tabela de Decomposição do Tempo de Execução**

| Fase | Trecho do código | Complexidade | Fração estimada | Classificação   |
| :---- | :---- | :---- | :---- | :---- |
| Fase 1: Inicialização | for (int i \= 0; i \< N\*N; i++) a\[i\] \= ... | O(N²) | ≈ 0,2% | Overhead sequencial negligenciável |
| Fase 2: Convolução 2D | Laço triplo P × Y × X | O(P × N²) | **≈ 99,6%** | **Hotspot crítico** |
| Fase 3: Checksum final | for (int i \= 0; i \< N\*N; i++) soma \+= a\[i\] | O(N²) | ≈ 0,2% | Redução sequencial final |

**Resultado da Estimativa:** A Fase 2 (processamento do laço triplo de convolução) possui estimativa teórica de dominar mais de 99,5% do tempo total de execução. A confirmação empírica dessa distribuição será obtida no perfilamento com a instrumentação de hardware e gprof/perf.

## **4\. Estimativa Teórica de Aceleração pela Lei de Amdahl**

A Lei de Amdahl estabelece o limite teórico do ganho de velocidade (Speedup) obtido pela paralelização de um código em função da sua fração paralelizável estimada (f) e do número de unidades de processamento (Np).

### **4.1 Formulação Matemática**

*S(Np) \= 1 / \[ (1 \- f) \+ (f / Np) \]*

Com base na estimativa teórica de hotspots, adota-se a fração paralelizável de **f \= 0,996** (99,6%), resultando em uma fração estritamente sequencial não paralelizável de **(1 \- f) \= 0,004** (0,4%).

### **4.2 Projeções de Speedup Teórico Máximo**

* **Ambiente Quad-Core (Np \= 4 threads/processos):**  
  S(4) \= 1 / \[ 0,004 \+ (0,996 / 4\) \] \= 1 / \[ 0,004 \+ 0,249 \] \= 1 / 0,253 ≈ **3,95x**  
* **Ambiente Octa-Core (Np \= 8 threads/processos):**  
  S(8) \= 1 / \[ 0,004 \+ (0,996 / 8\) \] \= 1 / \[ 0,004 \+ 0,1245 \] \= 1 / 0,1285 ≈ **7,78x**  
* **Limite Teórico Assintótico (Np → ∞):**  
  S\_max \= lim Np→∞ S(Np) \= 1 / (1 \- f) \= 1 / 0,004 \= **250x**

## **5\. Metodologia e Protocolo Experimental de Medição**

Para garantir reprodutibilidade, eliminar interferências do sistema operacional e assegurar um rigor científico compatível com os requisitos da disciplina, institui-se o seguinte protocolo de medição para a coleta do baseline:

### **5.1 Protocolo de Coleta de Dados**

1. **Execução de aquecimento (Warm-up):** Para cada tamanho de entrada, uma execução preliminar será realizada e descartada das amostras estatísticas. O objetivo é reduzir efeitos transitórios associados à inicialização, alocação de memória e carregamento inicial de dados. A eficácia desse procedimento será considerada na interpretação dos resultados.  
2. **Amostragem Mínima:** Serão coletadas exatamente **K \= 10 repetições independentes** para cada dimensão de imagem N ∈ {1000, 2000, 4000} com P \= 30 passes.  
3. **Métricas Estatísticas:** Os tempos reportados serão compostos pela Média Aritmética (μ), Desvio Padrão (σ) e Coeficiente de Variação (CV \= (σ / μ) \* 100%). Caso o CV ultrapasse 3%, a execução será investigada e, quando identificada interferência externa significativa, o conjunto será reexecutado.  
4. **Instrumentação Temporal:** Utilização da chamada de sistema de alta resolução clock\_gettime(CLOCK\_MONOTONIC) em C++, imune a ajustes dinâmicos do relógio de sistema (NTP).

## **6\. Plano Teórico de Paralelização**

A partir dos resultados e estimativas do baseline, estabelece-se o planejamento conceitual para as etapas subsequentes do projeto:

### **6.1 Estratégia OpenMP (Memória Compartilhada)**

* **Padrão Aplicado:** Paralelização do laço externo de espaço (eixo Y) utilizando a diretiva \#pragma omp parallel for dentro de cada passe p.  
* **Escalonamento:** Utilização de schedule(static), dado que a carga de computação por linha da imagem é homogênea (todos os pixels exigem exatamente 9 operações).  
* **Tratamento de Condições de Corrida:** Não há condição de corrida na gravação da imagem B, pois o particionamento das linhas Y atribui intervalos exclusivos de gravação para cada thread. A leitura do buffer A também é segura, pois todas as threads realizam apenas operações de leitura sobre o mesmo estado de entrada durante o passe. A sincronização de barreira implícita no final da diretiva garante a consistência antes da execução de a.swap(b).

### **6.2 Estratégia MPI (Memória Distribuída)**

* **Decomposição de Domínio:** Particionamento 1D em faixas horizontais de altura H\_local ≈ N / num\_procs.  
* **Distribuição Inicial:** A distribuição inicial dos blocos locais poderá ser realizada via MPI\_Scatter (ou MPI\_Scatterv), com posterior organização das regiões locais e halos necessários para o processamento.  
* **Troca de Halos (Bordas Fantasma):** Troca de 1 linha de borda superior e 1 linha de borda inferior entre processos vizinhos adjacentes a cada passe p via MPI\_Sendrecv (ou comunicação não-bloqueante MPI\_Irecv/MPI\_Isend).  
* **Operações Coletivas:** Consolidação da imagem final pelo nó mestre (Rank 0\) via MPI\_Gather (ou MPI\_Gatherv) e computação do checksum via MPI\_Reduce com operador MPI\_SUM.