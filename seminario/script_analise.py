#!/usr/bin/env python3
"""Gera gráficos SVG da campanha de medição, sem executar novas medições."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from html import escape
from pathlib import Path
import statistics
from typing import Callable

from script_medicao import validar_arquivos_campanha


RAIZ_PROJETO = Path(__file__).resolve().parent
CORES = ("#2563eb", "#dc2626", "#059669", "#9333ea", "#d97706", "#0891b2")


@dataclass(frozen=True)
class Grafico:
    """Contrato de um gráfico produzido a partir das métricas da campanha."""

    arquivo: str
    implementacoes: tuple[str, ...]
    campo: str
    campo_eixo_x: str
    campos_serie: tuple[str, ...]
    titulo: str
    rotulo_eixo_x: str
    rotulo_eixo_y: str
    referencia_ideal: Callable[[float], float] | None = None


GRAFICOS = (
    Grafico(
        "baseline/graficos/tempo.svg", ("baseline",), "tp_mediana_s", "n",
        ("implementacao",), "Tempo mediano — baseline", "Tamanho da imagem (N)", "Tempo (s)",
    ),
    Grafico(
        "openmp/graficos/tempo.svg", ("openmp",), "tp_mediana_s", "unidades",
        ("n", "escalonamento"), "Tempo mediano — OpenMP", "Threads", "Tempo (s)",
    ),
    Grafico(
        "openmp/graficos/speedup.svg", ("openmp",), "speedup", "unidades",
        ("n", "escalonamento"), "Speedup — OpenMP", "Threads", "Speedup",
        lambda unidades: unidades,
    ),
    Grafico(
        "openmp/graficos/eficiencia.svg", ("openmp",), "eficiencia", "unidades",
        ("n", "escalonamento"), "Eficiência — OpenMP", "Threads", "Eficiência",
        lambda _unidades: 1.0,
    ),
    Grafico(
        "mpi/graficos/tempo.svg", ("mpi",), "tp_mediana_s", "unidades",
        ("n",), "Tempo mediano — MPI", "Processos MPI", "Tempo (s)",
    ),
    Grafico(
        "mpi/graficos/speedup.svg", ("mpi",), "speedup", "unidades",
        ("n",), "Speedup — MPI", "Processos MPI", "Speedup",
        lambda unidades: unidades,
    ),
    Grafico(
        "mpi/graficos/eficiencia.svg", ("mpi",), "eficiencia", "unidades",
        ("n",), "Eficiência — MPI", "Processos MPI", "Eficiência",
        lambda _unidades: 1.0,
    ),
    Grafico(
        "mpi/graficos/comunicacao.svg", ("mpi",), "comunicacao_mediana_s", "unidades",
        ("n",), "Comunicação MPI", "Processos MPI", "Tempo (s)",
    ),
    Grafico(
        "mpi/graficos/computacao.svg", ("mpi",), "computacao_mediana_s", "unidades",
        ("n",), "Computação MPI", "Processos MPI", "Tempo (s)",
    ),
    Grafico(
        "graficos/tempo_comparativo.svg", ("openmp", "mpi"), "tp_mediana_s", "unidades",
        ("implementacao", "n", "escalonamento"), "Tempo mediano — OpenMP × MPI",
        "Unidades paralelas", "Tempo (s)",
    ),
    Grafico(
        "graficos/speedup_comparativo.svg", ("openmp", "mpi"), "speedup", "unidades",
        ("implementacao", "n", "escalonamento"), "Speedup — OpenMP × MPI",
        "Unidades paralelas", "Speedup", lambda unidades: unidades,
    ),
    Grafico(
        "graficos/eficiencia_comparativa.svg", ("openmp", "mpi"), "eficiencia", "unidades",
        ("implementacao", "n", "escalonamento"), "Eficiência — OpenMP × MPI",
        "Unidades paralelas", "Eficiência", lambda _unidades: 1.0,
    ),
)


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    """Lê um CSV UTF-8 produzido por script_medicao.py."""
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def validar_campanha(raiz: Path) -> None:
    """Impede gráficos a partir de uma campanha parcial ou inconsistente."""
    if (raiz / "dados/.campanha_em_andamento").exists():
        raise RuntimeError(
            "Campanha incompleta; conclua script_medicao.py antes de gerar gráficos"
        )
    validar_arquivos_campanha(raiz)


def enriquecer_metricas_mpi(
    metricas: list[dict[str, str]], raiz: Path
) -> list[dict[str, str]]:
    """Acrescenta às métricas MPI as medianas de comunicação e computação."""
    if not any(linha["implementacao"] == "mpi" for linha in metricas):
        return metricas

    overhead = ler_csv(raiz / "mpi/dados/mpi_overhead.csv")
    metricas_enriquecidas = []
    for linha in metricas:
        if linha["implementacao"] != "mpi":
            metricas_enriquecidas.append(linha)
            continue

        amostras = [
            amostra for amostra in overhead
            if all(
                amostra[campo] == linha[campo]
                for campo in ("n", "passes", "unidades", "escalonamento", "checksum")
            )
        ]
        if not amostras:
            raise RuntimeError(
                "Overhead ausente para uma configuração MPI; repita a campanha"
            )
        metricas_enriquecidas.append(
            {
                **linha,
                "comunicacao_mediana_s": str(statistics.median(
                    float(amostra["comunicacao_s"]) for amostra in amostras
                )),
                "computacao_mediana_s": str(statistics.median(
                    float(amostra["computacao_s"]) for amostra in amostras
                )),
            }
        )
    return metricas_enriquecidas


def rotulo_serie(campos: tuple[str, ...], valores: tuple[str, ...]) -> str:
    """Converte a chave de uma série em um rótulo legível."""
    partes = []
    for campo, valor in zip(campos, valores):
        if campo == "implementacao":
            partes.append("Baseline" if valor == "baseline" else valor.upper())
        elif campo == "n":
            partes.append(f"N={valor}")
        elif valor:
            partes.append(valor)
    return " — ".join(partes)


def gerar_curva(grafico: Grafico, linhas: list[dict[str, str]], raiz: Path) -> None:
    """Gera um SVG para uma especificação declarada em GRAFICOS."""
    amostras = [
        linha for linha in linhas if linha["implementacao"] in grafico.implementacoes
    ]
    if not amostras:
        return

    valores_x = sorted({float(linha[grafico.campo_eixo_x]) for linha in amostras})
    minimo_x, maximo_x = min(valores_x), max(valores_x)
    valores_y = [float(linha[grafico.campo]) for linha in amostras]
    if grafico.referencia_ideal is not None:
        valores_y.extend(grafico.referencia_ideal(valor) for valor in valores_x)
    maximo_y = max(max(valores_y), 0.01) * 1.1

    def posicao_x(valor: float) -> float:
        return 75 + 640 * (valor - minimo_x) / max(1, maximo_x - minimo_x)

    def posicao_y(valor: float) -> float:
        return 370 - 295 * valor / maximo_y

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="920" height="440" viewBox="0 0 920 440">',
        '<rect width="920" height="440" fill="white"/>',
        f'<text x="75" y="30" font-family="sans-serif" font-size="20">{escape(grafico.titulo)}</text>',
        '<path d="M75 65V370H715" fill="none" stroke="black"/>',
        f'<text x="340" y="425" font-family="sans-serif">{escape(grafico.rotulo_eixo_x)}</text>',
        f'<text x="8" y="55" font-family="sans-serif">{escape(grafico.rotulo_eixo_y)}</text>',
    ]
    for indice in range(6):
        valor = maximo_y * indice / 5
        svg.append(
            f'<text x="8" y="{posicao_y(valor) + 5:.1f}" '
            f'font-family="sans-serif">{valor:.2f}</text>'
        )
    for valor_x in valores_x:
        rotulo = str(int(valor_x)) if valor_x.is_integer() else str(valor_x)
        svg.append(
            f'<text x="{posicao_x(valor_x):.1f}" y="395" '
            f'font-family="sans-serif">{rotulo}</text>'
        )
    if grafico.referencia_ideal is not None:
        svg.append(
            f'<path d="M{posicao_x(minimo_x)} {posicao_y(grafico.referencia_ideal(minimo_x))} '
            f'L{posicao_x(maximo_x)} {posicao_y(grafico.referencia_ideal(maximo_x))}" '
            'stroke="gray" stroke-dasharray="5 5"/>'
        )
        svg.append('<text x="745" y="65" font-family="sans-serif">Ideal (tracejado)</text>')

    chaves = sorted({
        tuple(linha[campo] for campo in grafico.campos_serie) for linha in amostras
    })
    for indice, chave in enumerate(chaves):
        serie = sorted(
            (
                linha for linha in amostras
                if tuple(linha[campo] for campo in grafico.campos_serie) == chave
            ),
            key=lambda linha: float(linha[grafico.campo_eixo_x]),
        )
        cor = CORES[indice % len(CORES)]
        pontos = " ".join(
            f"{posicao_x(float(linha[grafico.campo_eixo_x])):.2f},"
            f"{posicao_y(float(linha[grafico.campo])):.2f}"
            for linha in serie
        )
        svg.append(f'<polyline points="{pontos}" fill="none" stroke="{cor}" stroke-width="2"/>')
        for linha in serie:
            svg.append(
                f'<circle cx="{posicao_x(float(linha[grafico.campo_eixo_x])):.2f}" '
                f'cy="{posicao_y(float(linha[grafico.campo])):.2f}" r="4" fill="{cor}"/>'
            )
        svg.append(
            f'<text x="745" y="{95 + indice * 25}" fill="{cor}" font-family="sans-serif">'
            f'{escape(rotulo_serie(grafico.campos_serie, chave))}</text>'
        )

    caminho = raiz / grafico.arquivo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(svg + ["</svg>"]), encoding="utf-8")


def gerar_graficos(raiz: Path = RAIZ_PROJETO) -> None:
    """Consome a campanha oficial sem recompilar ou executar medições."""
    validar_campanha(raiz)
    metricas = enriquecer_metricas_mpi(ler_csv(raiz / "dados/metricas.csv"), raiz)
    if not metricas:
        raise RuntimeError("Sem métricas; execute python3 script_medicao.py primeiro")
    for grafico in GRAFICOS:
        gerar_curva(grafico, metricas, raiz)
    print(f"Gráficos SVG: {raiz / 'graficos'} e pastas de cada implementação")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    gerar_graficos()


if __name__ == "__main__":
    main()
