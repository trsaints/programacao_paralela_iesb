#!/usr/bin/env python3
"""Executa medições reproduzíveis do baseline, OpenMP e MPI.

O baseline é obrigatório. OpenMP e MPI são opcionais enquanto suas fontes ou
ferramentas de compilação/execução não estiverem disponíveis; nesses casos o
script registra o motivo em ``dados/execucoes_ignoradas.csv``.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parent
DIRETORIO_DADOS_COMPARTILHADOS = RAIZ_PROJETO / "dados"

TAMANHOS_MATRIZ = (1024, 2048, 4096)
PASSES = 30
AQUECIMENTOS = 1
REPETICOES = 10


def unidades_disponiveis(implementacao: Implementacao, testar_slots: bool = False) -> tuple[int, ...]:
    """Limita a campanha às CPUs permitidas ao processo/contêiner."""
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    candidatas = tuple(u for u in implementacao.unidades if u <= cpus)
    if not testar_slots or not implementacao.usa_mpi:
        return candidatas
    disponiveis = []
    for unidades in candidatas:
        # Testa a política real do lançador, sem forçar oversubscription.
        resultado = subprocess.run(
            ["mpirun", "-np", str(unidades), sys.executable, "-c", "pass"],
            capture_output=True, text=True, check=False,
        )
        if resultado.returncode == 0:
            disponiveis.append(unidades)
        elif "not enough slots" in (resultado.stderr + resultado.stdout).lower():
            print(f"mpi: processos={unidades} SKIPPED — slots MPI insuficientes", flush=True)
        else:
            raise RuntimeError(f"Falha ao verificar slots MPI: {resultado.stderr or resultado.stdout}")
    if not disponiveis:
        raise RuntimeError("Nenhuma configuração MPI possui slots disponíveis")
    return tuple(disponiveis)

PADRAO_SAIDA = re.compile(
    r"N=(?P<n>\d+)\s+passes=(?P<passes>\d+)\s+"
    r"checksum=(?P<checksum>[+-]?\d+(?:\.\d+)?)\s+"
    r"tempo=(?P<tempo>[+-]?\d+(?:\.\d+)?)\s+s"
)


@dataclass(frozen=True)
class Implementacao:
    """Contrato de compilação e execução de uma versão do algoritmo."""

    nome: str
    tipo_unidade: str
    unidades: tuple[int, ...]
    fonte: Path
    executavel: Path
    compilador: str
    flags_compilacao: tuple[str, ...] = ()
    escalonamento: str = ""
    usa_mpi: bool = False
    obrigatoria: bool = False

    def comando_compilacao(self) -> list[str]:
        return [
            self.compilador,
            "-O2",
            *self.flags_compilacao,
            "-o",
            str(self.executavel),
            str(self.fonte),
        ]


# Quando as versões paralelas forem implementadas, mantenha esta interface:
#   <executável> N PASSES
# e imprima uma única linha no formato N=... passes=... checksum=... tempo=... s.
# Ajuste os nomes de fonte/executável aqui somente se o grupo escolher outros nomes.
IMPLEMENTACOES = (
    Implementacao(
        nome="baseline",
        tipo_unidade="serial",
        unidades=(1,),
        fonte=RAIZ_PROJETO / "baseline" / "04_convolucao.cpp",
        executavel=RAIZ_PROJETO / "baseline" / "convolucao.out",
        compilador="g++",
        obrigatoria=True,
    ),
    Implementacao(
        nome="openmp",
        tipo_unidade="threads",
        unidades=(1, 2, 4, 8),
        fonte=RAIZ_PROJETO / "openmp" / "04_convolucao_openmp.cpp",
        executavel=RAIZ_PROJETO / "openmp" / "convolucao_openmp.out",
        compilador="g++",
        flags_compilacao=("-fopenmp",),
        escalonamento="static",
    ),
    Implementacao(
        nome="mpi",
        tipo_unidade="processos",
        unidades=(1, 2, 4, 8),
        fonte=RAIZ_PROJETO / "mpi" / "04_convolucao_mpi.cpp",
        executavel=RAIZ_PROJETO / "mpi" / "convolucao_mpi.out",
        compilador="mpic++",
        usa_mpi=True,
    ),
)

COLUNAS_MEDICOES = (
    "implementacao",
    "tipo_unidade",
    "unidades",
    "escalonamento",
    "n",
    "passes",
    "repeticao",
    "checksum",
    "tempo_s",
)

COLUNAS_RESUMO = (
    "implementacao",
    "tipo_unidade",
    "unidades",
    "escalonamento",
    "n",
    "passes",
    "repeticoes",
    "checksum",
    "tempo_medio_s",
    "tempo_mediano_s",
    "desvio_padrao_s",
)

COLUNAS_METRICAS = (
    "implementacao",
    "tipo_unidade",
    "unidades",
    "escalonamento",
    "n",
    "passes",
    "checksum",
    "t1_mediana_s",
    "tp_mediana_s",
    "speedup",
    "eficiencia",
)

COLUNAS_IGNORADAS = (
    "implementacao",
    "tipo_unidade",
    "fonte",
    "executavel",
    "motivo",
)


def resumir_erro(texto: str) -> str:
    """Normaliza mensagens para uma célula CSV e para o terminal."""
    linhas = [linha.strip() for linha in texto.splitlines()
              if linha.strip() and set(linha.strip()) != {"-"}]
    return linhas[0] if linhas else "sem detalhes fornecidos"


def motivo_indisponibilidade(implementacao: Implementacao) -> str | None:
    """Retorna o motivo de indisponibilidade sem tentar compilar nada."""
    if not implementacao.fonte.is_file():
        return f"fonte não encontrada: {implementacao.fonte.relative_to(RAIZ_PROJETO)}"

    if shutil.which(implementacao.compilador) is None:
        return f"compilador não encontrado no PATH: {implementacao.compilador}"

    if implementacao.usa_mpi and shutil.which("mpirun") is None:
        return "lançador MPI não encontrado no PATH: mpirun"

    return None


def preparar_implementacao(implementacao: Implementacao) -> str | None:
    """Compila uma implementação e retorna motivo de skip, se aplicável."""
    motivo = motivo_indisponibilidade(implementacao)
    if motivo is not None:
        return motivo

    implementacao.executavel.parent.mkdir(parents=True, exist_ok=True)
    resultado = subprocess.run(
        implementacao.comando_compilacao(),
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
        check=False,
    )

    if resultado.returncode != 0:
        detalhe = resumir_erro(resultado.stderr or resultado.stdout)
        return f"compilação falhou: {detalhe}"

    if not implementacao.executavel.is_file():
        return "compilação terminou sem gerar o executável esperado"

    return None


def comando_execucao(
    implementacao: Implementacao,
    tamanho: int,
    unidades: int,
) -> tuple[list[str], dict[str, str]]:
    """Monta o comando e o ambiente de uma execução de medição."""
    comando: list[str] = []
    ambiente = os.environ.copy()

    if implementacao.usa_mpi:
        comando.extend(("mpirun", "-np", str(unidades)))

    if implementacao.nome == "openmp":
        ambiente["OMP_NUM_THREADS"] = str(unidades)
        ambiente["OMP_DYNAMIC"] = "FALSE"
        if implementacao.escalonamento:
            ambiente["OMP_SCHEDULE"] = implementacao.escalonamento

    comando.extend((str(implementacao.executavel), str(tamanho), str(PASSES)))
    if implementacao.usa_mpi:
        comando.append("--validate")
    return comando, ambiente


def interpretar_saida(
    stdout: str,
    implementacao: Implementacao,
    tamanho_esperado: int,
) -> tuple[str, float]:
    """Valida e interpreta a linha de resultado padronizada do executável."""
    correspondencias = [
        PADRAO_SAIDA.fullmatch(linha.strip())
        for linha in stdout.splitlines()
        if PADRAO_SAIDA.fullmatch(linha.strip()) is not None
    ]

    if len(correspondencias) != 1:
        raise RuntimeError(
            f"{implementacao.nome}: esperada exatamente uma linha de resultado; "
            f"saída recebida: {stdout.strip()!r}"
        )

    dados = correspondencias[0]
    assert dados is not None
    tamanho_obtido = int(dados.group("n"))
    passes_obtidos = int(dados.group("passes"))

    if tamanho_obtido != tamanho_esperado or passes_obtidos != PASSES:
        raise RuntimeError(
            f"{implementacao.nome}: parâmetros retornados inesperados: "
            f"N={tamanho_obtido}, passes={passes_obtidos}"
        )

    return dados.group("checksum"), float(dados.group("tempo"))


def executar_uma_vez(
    implementacao: Implementacao,
    tamanho: int,
    unidades: int,
    detalhes: dict | None = None,
) -> tuple[str, float]:
    """Executa uma configuração e devolve checksum e tempo medido."""
    comando, ambiente = comando_execucao(implementacao, tamanho, unidades)
    resultado = subprocess.run(
        comando,
        cwd=RAIZ_PROJETO,
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )

    if resultado.returncode != 0:
        detalhe = (resultado.stderr or resultado.stdout).strip()
        raise RuntimeError(
            f"{implementacao.nome}: execução falhou (código {resultado.returncode}): "
            f"{detalhe}"
        )

    medicao = interpretar_saida(resultado.stdout, implementacao, tamanho)
    if implementacao.usa_mpi:
        if "validacao=OK" not in resultado.stderr.splitlines():
            raise RuntimeError("MPI não confirmou a validação integral")
        tempos = re.search(r"comunicacao_s=([\d.]+) computacao_s=([\d.]+)", resultado.stderr)
        if tempos is None:
            raise RuntimeError("Tempos de comunicação/computação MPI ausentes")
        if detalhes is not None:
            detalhes.update(comunicacao_s=float(tempos[1]), computacao_s=float(tempos[2]))
    return medicao


def medir_implementacao(
    implementacao: Implementacao,
    referencias_baseline: dict[tuple[int, int], str],
    writer_medicoes: csv.DictWriter,
    writer_resumo: csv.DictWriter,
    writer_metricas: csv.DictWriter,
    writer_overhead: csv.DictWriter | None = None,
) -> None:
    """Executa aquecimento, repetições, validação e estatísticas de uma versão."""
    for unidades in unidades_disponiveis(implementacao, testar_slots=True):
        for tamanho in TAMANHOS_MATRIZ:
            descricao = (
                f"{implementacao.nome}: N={tamanho}, passes={PASSES}, "
                f"{implementacao.tipo_unidade}={unidades}"
            )
            print(f"Medindo {descricao}", flush=True)

            for _ in range(AQUECIMENTOS):
                executar_uma_vez(implementacao, tamanho, unidades)

            checksum_esperado = referencias_baseline.get((tamanho, PASSES))
            tempos: list[float] = []

            for repeticao in range(1, REPETICOES + 1):
                detalhes: dict = {}
                checksum, tempo_s = executar_uma_vez(
                    implementacao, tamanho, unidades, detalhes
                )

                if checksum_esperado is None:
                    checksum_esperado = checksum
                    if implementacao.nome == "baseline":
                        referencias_baseline[(tamanho, PASSES)] = checksum
                elif checksum != checksum_esperado:
                    raise RuntimeError(
                        f"{implementacao.nome}: checksum divergente em N={tamanho}, "
                        f"{implementacao.tipo_unidade}={unidades}, "
                        f"repetição={repeticao}: esperado {checksum_esperado}, "
                        f"obtido {checksum}"
                    )

                tempos.append(tempo_s)
                linha_medicao = {
                    "implementacao": implementacao.nome,
                    "tipo_unidade": implementacao.tipo_unidade,
                    "unidades": unidades,
                    "escalonamento": implementacao.escalonamento,
                    "n": tamanho,
                    "passes": PASSES,
                    "repeticao": repeticao,
                    "checksum": checksum,
                    "tempo_s": tempo_s,
                }
                writer_medicoes.writerow(linha_medicao)
                if implementacao.usa_mpi and writer_overhead is not None:
                    writer_overhead.writerow({**linha_medicao, **detalhes})

            assert checksum_esperado is not None
            tempo_medio = statistics.mean(tempos)
            tempo_mediano = statistics.median(tempos)
            desvio_padrao = statistics.stdev(tempos)
            linha_resumo = {
                "implementacao": implementacao.nome,
                "tipo_unidade": implementacao.tipo_unidade,
                "unidades": unidades,
                "escalonamento": implementacao.escalonamento,
                "n": tamanho,
                "passes": PASSES,
                "repeticoes": REPETICOES,
                "checksum": checksum_esperado,
                "tempo_medio_s": tempo_medio,
                "tempo_mediano_s": tempo_mediano,
                "desvio_padrao_s": desvio_padrao,
            }
            writer_resumo.writerow(linha_resumo)

            referencia = referencias_baseline[(tamanho, PASSES)]
            if checksum_esperado != referencia:
                raise RuntimeError(
                    f"{implementacao.nome}: checksum não coincide com o baseline "
                    f"em N={tamanho}: esperado {referencia}, obtido {checksum_esperado}"
                )

            t1 = tempo_mediano if implementacao.nome == "baseline" else None
            if t1 is None:
                # A implementação baseline é processada antes das demais.
                # Sua mediana já foi registrada no mapa abaixo.
                t1 = tempos_referencia[(tamanho, PASSES)]
            else:
                tempos_referencia[(tamanho, PASSES)] = t1

            speedup = t1 / tempo_mediano
            eficiencia = speedup / unidades
            writer_metricas.writerow(
                {
                    "implementacao": implementacao.nome,
                    "tipo_unidade": implementacao.tipo_unidade,
                    "unidades": unidades,
                    "escalonamento": implementacao.escalonamento,
                    "n": tamanho,
                    "passes": PASSES,
                    "checksum": checksum_esperado,
                    "t1_mediana_s": t1,
                    "tp_mediana_s": tempo_mediano,
                    "speedup": speedup,
                    "eficiencia": eficiencia,
                }
            )


# Medianas do baseline da campanha atual. É preenchido antes de OpenMP/MPI.
tempos_referencia: dict[tuple[int, int], float] = {}


def mostrar_plano() -> None:
    """Mostra fontes esperadas e skips possíveis sem compilar ou medir."""
    for implementacao in IMPLEMENTACOES:
        print(f"{implementacao.nome}: unidades disponíveis={unidades_disponiveis(implementacao)}")
        motivo = motivo_indisponibilidade(implementacao)
        if motivo is None:
            print(
                f"{implementacao.nome}: PRONTO PARA COMPILAR "
                f"({implementacao.fonte.relative_to(RAIZ_PROJETO)})"
            )
        else:
            estado = "ERRO" if implementacao.obrigatoria else "SKIPPED"
            print(f"{implementacao.nome}: {estado} — {motivo}")


def validar_arquivos_campanha(raiz: Path) -> None:
    """Confere a persistência das amostras antes de liberar os gráficos."""
    def ler(caminho):
        with caminho.open(newline="", encoding="utf-8") as arquivo:
            return list(csv.DictReader(arquivo))

    for nome in {l["implementacao"] for l in ler(raiz / "dados/metricas.csv")}:
        medicoes = ler(raiz / nome / "dados" / f"{nome}_medicoes.csv")
        resumos = ler(raiz / nome / "dados" / f"{nome}_resumo.csv")
        for resumo in resumos:
            amostras = [l for l in medicoes if all(l[c] == resumo[c] for c in
                        ("implementacao", "n", "passes", "unidades", "escalonamento", "checksum"))]
            esperadas = int(resumo["repeticoes"])
            if len(amostras) != esperadas or {int(l["repeticao"]) for l in amostras} != set(range(1, esperadas + 1)):
                raise RuntimeError(f"CSV incompleto: {nome}, N={resumo['n']}, unidades={resumo['unidades']}")
        if len(medicoes) != sum(int(l["repeticoes"]) for l in resumos):
            raise RuntimeError(f"CSV de medições/resumo inconsistente: {nome}")


def executar_campanha() -> None:
    """Compila e mede todas as implementações disponíveis."""
    if REPETICOES < 2:
        raise ValueError("REPETICOES deve ser pelo menos 2 para calcular desvio-padrão")

    DIRETORIO_DADOS_COMPARTILHADOS.mkdir(parents=True, exist_ok=True)
    marcador = DIRETORIO_DADOS_COMPARTILHADOS / ".campanha_em_andamento"
    marcador.write_text("Campanha incompleta; execute script_medicao.py novamente.\n", encoding="utf-8")
    (RAIZ_PROJETO / "mpi" / "dados").mkdir(parents=True, exist_ok=True)
    tempos_referencia.clear()
    referencias_baseline: dict[tuple[int, int], str] = {}

    with (
        (RAIZ_PROJETO / "mpi/dados/mpi_overhead.csv").open(
            "w", newline="", encoding="utf-8"
        ) as arquivo_overhead,
        (DIRETORIO_DADOS_COMPARTILHADOS / "metricas.csv").open(
            "w", newline="", encoding="utf-8"
        ) as arquivo_metricas,
        (DIRETORIO_DADOS_COMPARTILHADOS / "execucoes_ignoradas.csv").open(
            "w", newline="", encoding="utf-8"
        ) as arquivo_ignoradas,
    ):
        writer_metricas = csv.DictWriter(
            arquivo_metricas, fieldnames=COLUNAS_METRICAS, lineterminator="\n"
        )
        writer_overhead = csv.DictWriter(
            arquivo_overhead,
            fieldnames=(*COLUNAS_MEDICOES, "comunicacao_s", "computacao_s"),
            lineterminator="\n",
        )
        writer_overhead.writeheader()
        writer_ignoradas = csv.DictWriter(
            arquivo_ignoradas, fieldnames=COLUNAS_IGNORADAS, lineterminator="\n"
        )
        writer_metricas.writeheader()
        writer_ignoradas.writeheader()

        for implementacao in IMPLEMENTACOES:
            motivo = preparar_implementacao(implementacao)
            if motivo is not None:
                if implementacao.obrigatoria:
                    raise RuntimeError(f"baseline indisponível: {motivo}")

                print(f"{implementacao.nome}: SKIPPED — {motivo}")
                writer_ignoradas.writerow(
                    {
                        "implementacao": implementacao.nome,
                        "tipo_unidade": implementacao.tipo_unidade,
                        "fonte": implementacao.fonte.relative_to(RAIZ_PROJETO),
                        "executavel": implementacao.executavel.relative_to(RAIZ_PROJETO),
                        "motivo": motivo,
                    }
                )
                continue

            diretorio_dados_implementacao = implementacao.fonte.parent / "dados"
            diretorio_dados_implementacao.mkdir(parents=True, exist_ok=True)
            with (
                (diretorio_dados_implementacao / f"{implementacao.nome}_medicoes.csv").open(
                    "w", newline="", encoding="utf-8"
                ) as arquivo_medicoes,
                (diretorio_dados_implementacao / f"{implementacao.nome}_resumo.csv").open(
                    "w", newline="", encoding="utf-8"
                ) as arquivo_resumo,
            ):
                writer_medicoes = csv.DictWriter(
                    arquivo_medicoes,
                    fieldnames=COLUNAS_MEDICOES,
                    lineterminator="\n",
                )
                writer_resumo = csv.DictWriter(
                    arquivo_resumo,
                    fieldnames=COLUNAS_RESUMO,
                    lineterminator="\n",
                )
                writer_medicoes.writeheader()
                writer_resumo.writeheader()
                medir_implementacao(
                    implementacao,
                    referencias_baseline=referencias_baseline,
                    writer_medicoes=writer_medicoes,
                    writer_resumo=writer_resumo,
                    writer_metricas=writer_metricas,
                    writer_overhead=writer_overhead,
                )

    validar_arquivos_campanha(RAIZ_PROJETO)
    marcador.unlink()
    print("\nPerfilamento finalizado.")
    print(f"Métricas comparativas: {DIRETORIO_DADOS_COMPARTILHADOS / 'metricas.csv'}")
    print(
        "Execuções ignoradas: "
        f"{DIRETORIO_DADOS_COMPARTILHADOS / 'execucoes_ignoradas.csv'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mede baseline, OpenMP e MPI quando estiverem disponíveis."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="mostra as fontes esperadas sem compilar nem executar medições",
    )
    argumentos = parser.parse_args()

    if argumentos.dry_run:
        mostrar_plano()
        return

    executar_campanha()


if __name__ == "__main__":
    main()
