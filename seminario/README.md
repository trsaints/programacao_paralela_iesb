# Projeto Acadêmico — Programação Paralela (CCO085)

Este diretório é a raiz do projeto de **convolução 2D (blur)** do grupo. Ele é
autônomo: abra `seminario/` no VS Code ou entre nele antes de usar `make` e os
demais comandos deste guia.

O algoritmo sequencial de referência fornecido pelo professor está preservado
em `baseline/04_convolucao.cpp`. As versões OpenMP e MPI deverão produzir o
mesmo checksum para a mesma entrada, sem alterar a lógica nem a entrada do
baseline.

## Situação

| Item exigido | Situação |
| --- | --- |
| Baseline sequencial | disponível em `baseline/` |
| Makefile unificado | disponível |
| Script de medição e CSV | disponível |
| OpenMP | estrutura preparada; fonte não implementada |
| MPI | faixas horizontais, halos, coletivas e validação integral disponíveis; veja [mpi/README.md](mpi/README.md) |
| Gráficos finais | aguardam dados paralelos válidos |
| `AUTORES.md` | disponível, mas deve ser preenchido pelo trio |

Os `SKIPPED` exibidos para fontes ou ferramentas ausentes são intencionais durante o
desenvolvimento. Eles **não** indicam que a entrega final está completa: antes
da entrega, as três fontes devem existir e `make check-final` deve terminar sem
erros.

## Ambiente de referência

O projeto foi preparado para o ambiente oficial da disciplina: Linux, `g++`,
OpenMP, OpenMPI, `make` e Python 3. As medições que serão apresentadas no
relatório e nos gráficos finais devem ser feitas no laboratório ou no contêiner
Docker equivalente da disciplina.

Os CSVs versionados podem ser gerados no Dev Container durante o
desenvolvimento, em um notebook pessoal. Eles são úteis como histórico e teste
inicial, mas não devem ser usados como números finais sem uma nova campanha no
laboratório, cujo hardware é a referência da disciplina. As configurações de
desenvolvimento estão documentadas em [`HARDWARE.md`](HARDWARE.md).

### Usar Docker

Os arquivos `Dockerfile` e `docker-compose.yml` reproduzem a base Ubuntu 24.04
e o conjunto de ferramentas de compilação do ambiente da disciplina. O
Dockerfile também instala `git`, apenas para o controle de versão funcionar no
Dev Container. O repositório local é montado diretamente no contêiner; não há
clone adicional. Na raiz deste projeto:

```sh
docker compose build
docker compose run --rm pp-lab
```

O shell abrirá em `/lab`, que é a mesma pasta `seminario/` do computador host.
Então execute, por exemplo:

```sh
make info
make baseline
python3 script_medicao.py --dry-run
```

Para trabalhar pelo VS Code e acompanhar o histórico Git completo, abra a raiz
do repositório e escolha **Dev Containers: Reopen in Container**. A configuração
em `../.devcontainer/` abre o repositório inteiro em `/workspace`; dentro do
terminal do contêiner, use `cd seminario` antes dos comandos deste guia.

Nenhuma dependência Python externa é necessária: o script usa somente a
biblioteca padrão. O número de CPUs visível para Docker determina os pontos de
threads/processos que podem ser medidos; confira-o com `nproc`.

## Compilação

No Dev Container, o terminal começa em `/workspace`. Entre no projeto e compile
o baseline com:

```sh
cd seminario
make baseline
```

Também é seguro executar `make`: ele compila o baseline e mostra `SKIPPED` para
OpenMP e MPI enquanto as fontes não existirem. Esses `SKIPPED` são o
comportamento esperado nessa condição.

| Comando | Quando usar |
| --- | --- |
| `make baseline` | compilar somente o sequencial |
| `make` | compilar todas as versões que já tenham fonte |
| `make openmp` / `make mpi` | depois que a respectiva fonte existir |
| `make clean` | somente quando quiser remover os executáveis gerados |
| `make check-final` | **somente antes da entrega**, quando as três fontes existirem |

`make check-final` falha de propósito enquanto exigir fontes inexistentes:
`openmp/04_convolucao_openmp.cpp` e `mpi/04_convolucao_mpi.cpp`.

O Makefile é a interface unificada para a compilação manual. O
`script_medicao.py` preserva sua automação própria e invoca diretamente `g++`
ou `mpic++` com as flags necessárias; esses compiladores fazem parte do
ambiente oficial.

As ferramentas podem ser substituídas apenas quando necessário, mantendo a
interface do Makefile:

```sh
make CXX=g++ MPICXX=mpic++
```

## Contrato das implementações

| Implementação | Fonte | Executável | Forma de executar |
| --- | --- | --- | --- |
| Baseline | `baseline/04_convolucao.cpp` | `baseline/convolucao.out` | `./baseline/convolucao.out N PASSES` |
| OpenMP | `openmp/04_convolucao_openmp.cpp` | `openmp/convolucao_openmp.out` | `OMP_NUM_THREADS=T ./openmp/convolucao_openmp.out N PASSES` |
| MPI | `mpi/04_convolucao_mpi.cpp` | `mpi/convolucao_mpi.out` | `mpirun -np P ./mpi/convolucao_mpi.out N PASSES` |

Cada executável deve aceitar `N` e `PASSES` e emitir exatamente uma linha de
resultado no formato abaixo. A versão MPI deve imprimi-la somente no rank 0.

```text
N=... passes=... checksum=... tempo=... s
```

O script compara o checksum de cada versão paralela com o checksum do baseline
na mesma campanha. Os detalhes específicos das versões futuras estão em
`openmp/README.md` e `mpi/README.md`.

## Medições e CSVs

Execute a campanha a partir desta pasta:

```sh
python3 script_medicao.py
```

O comando compila diretamente cada implementação disponível, descarta uma
execução de aquecimento e registra dez repetições válidas por configuração. Ele
sobrescreve os CSVs da campanha anterior; antes de uma campanha oficial,
confirme que você deseja substituir os dados de desenvolvimento versionados.

| Parâmetro padrão | Valor |
| --- | ---: |
| Tamanhos `N` | 1024, 2048 e 4096 |
| Passes | 30 |
| Aquecimento descartado | 1 por configuração |
| Repetições válidas | 10 por configuração |
| Unidades paralelas candidatas | 1, 2, 4 e 8, limitadas por `nproc` |
| Tempo de referência | mediana do baseline (`T1`) |

Para verificar fontes, ferramentas e unidades disponíveis sem compilar nem
alterar CSVs:

```sh
python3 script_medicao.py --dry-run
```

Os arquivos produzidos são:

```text
baseline/dados/baseline_medicoes.csv   # medições brutas do sequencial
baseline/dados/baseline_resumo.csv     # média, mediana e desvio-padrão
openmp/dados/openmp_medicoes.csv       # criado quando OpenMP estiver pronto
openmp/dados/openmp_resumo.csv
mpi/dados/mpi_medicoes.csv             # criado quando MPI estiver pronto
mpi/dados/mpi_resumo.csv
dados/metricas.csv                     # T1, Tp, speedup e eficiência
dados/execucoes_ignoradas.csv          # versões indisponíveis na campanha
```

A matriz automática de unidades mede **escalabilidade forte** para
cada tamanho fixo. A entrega final também exige análise de escalabilidade fraca:
quando OpenMP e MPI forem implementados, planejem e registrem uma campanha em
que o trabalho por unidade permaneça aproximadamente constante (por exemplo,
mantendo `N² / P` aproximadamente constante). Não apresente uma curva fraca
como concluída sem os dados brutos e a metodologia correspondente.

## Gráficos sem dependência externa

Importe os CSVs em LibreOffice Calc, Excel ou Google Sheets com codificação
UTF-8, separador vírgula e decimal ponto. Não há gerador de gráficos nem
biblioteca Python adicional no projeto.

| Gráfico | Dados de origem |
| --- | --- |
| Tempo do baseline por tamanho | `baseline/dados/baseline_resumo.csv`: `n` × `tempo_mediano_s` |
| Tempo OpenMP ou MPI | `<implementacao>/dados/<implementacao>_resumo.csv`: `unidades` × `tempo_mediano_s` |
| Speedup ou eficiência por implementação | `dados/metricas.csv`, filtrado por `implementacao` e `n` |
| Comparativo OpenMP × MPI | `dados/metricas.csv`, com séries separadas por implementação e `n` |

Versione gráficos específicos em cada implementação:

```text
baseline/graficos/
openmp/graficos/
mpi/graficos/
```

Coloque gráficos comparativos e gerais em `graficos/`, ao lado dos relatórios
gerais. Não crie imagens vazias: gere cada gráfico apenas após validar os dados
da implementação correspondente no ambiente oficial.

## Revisão antes da entrega e demonstração

1. Preencha `AUTORES.md` com os três integrantes e suas frentes técnicas.
2. Confirme que as fontes OpenMP e MPI existem e mantêm o resultado do
   baseline.
3. No contêiner/laboratório, execute `make clean && make check-final`.
4. Execute `python3 script_medicao.py` no mesmo ambiente e revise todos os
   checksums, CSVs e `SKIPPED` (não deve restar nenhum para as três versões).
5. Gere e versione gráficos de tempo, speedup, eficiência, escalabilidade forte
   e fraca, com metodologia e ambiente identificados.
6. Atualize o relatório com a máquina/contêiner, o número de CPUs visíveis e os
   resultados da campanha oficial.
7. Teste a demonstração ao vivo: baseline, OpenMP com várias threads, MPI com
   vários processos e pelo menos um gráfico de speedup.

O documento `relatorio_teorico.v2.md` preserva a análise e os dados de
desenvolvimento do baseline. Atualize-o somente após a campanha oficial, sem
misturar resultados de máquinas diferentes na mesma comparação.
