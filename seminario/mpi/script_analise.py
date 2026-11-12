#!/usr/bin/env python3
"""Campanha MPI com validação integral, CSV e curvas SVG (biblioteca padrão)."""
import argparse
import csv
from pathlib import Path
import re
import statistics
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from script_medicao import PADRAO_SAIDA


def executar(comando, n, passes, validar=False):
    resultado = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True,
                               check=True)
    linhas = [PADRAO_SAIDA.fullmatch(l.strip()) for l in resultado.stdout.splitlines()]
    dados = [m for m in linhas if m]
    if len(dados) != 1 or int(dados[0]['n']) != n or int(dados[0]['passes']) != passes:
        raise RuntimeError(f'Saída inválida: {resultado.stdout!r}')
    if validar and 'validacao=OK' not in resultado.stderr.splitlines():
        raise RuntimeError('MPI não confirmou a validação integral')
    tempos = re.search(r'comunicacao_s=([\d.]+) computacao_s=([\d.]+)', resultado.stderr)
    if validar and tempos is None:
        raise RuntimeError('Tempos MPI ausentes')
    return (dados[0]['checksum'], float(dados[0]['tempo']),
            float(tempos[1]) if tempos else 0.0,
            float(tempos[2]) if tempos else 0.0)


def curva(caminho, linhas, campo, titulo, ideal):
    """SVG independente: uma série por tamanho, e referência ideal tracejada."""
    cores = ('#2563eb', '#dc2626', '#059669', '#9333ea', '#d97706')
    xmax = max(int(l['processos']) for l in linhas)
    ymax = max([float(l[campo]) for l in linhas] + [ideal(xmax), 0.01]) * 1.1
    x = lambda v: 75 + 640 * (v - 1) / max(1, xmax - 1)
    y = lambda v: 370 - 295 * v / ymax
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="440" viewBox="0 0 920 440">',
           '<rect width="920" height="440" fill="white"/>',
           f'<text x="75" y="30" font-family="sans-serif" font-size="20">{titulo}</text>',
           '<path d="M75 65V370H715" fill="none" stroke="black"/>',
           '<text x="340" y="425" font-family="sans-serif">Processos MPI</text>']
    for i in range(6):
        valor = ymax * i / 5
        svg.append(f'<text x="8" y="{y(valor)+5:.1f}" font-family="sans-serif">{valor:.2f}</text>')
    for p in sorted({int(l['processos']) for l in linhas}):
        svg.append(f'<text x="{x(p):.1f}" y="395" font-family="sans-serif">{p}</text>')
    svg.append(f'<path d="M{x(1)} {y(ideal(1))}L{x(xmax)} {y(ideal(xmax))}" stroke="gray" stroke-dasharray="5 5"/>')
    svg.append('<text x="745" y="65" font-family="sans-serif">Ideal (tracejado)</text>')
    for indice, n in enumerate(sorted({int(l['n']) for l in linhas})):
        serie = sorted((l for l in linhas if int(l['n']) == n), key=lambda l: int(l['processos']))
        cor = cores[indice % len(cores)]
        pontos = ' '.join(f"{x(int(l['processos'])):.2f},{y(float(l[campo])):.2f}" for l in serie)
        svg.append(f'<polyline points="{pontos}" fill="none" stroke="{cor}" stroke-width="2"/>')
        for l in serie:
            svg.append(f'<circle cx="{x(int(l["processos"])):.2f}" cy="{y(float(l[campo])):.2f}" r="4" fill="{cor}"/>')
        svg.append(f'<text x="745" y="{95 + indice * 25}" fill="{cor}" font-family="sans-serif">N={n}</text>')
    caminho.write_text('\n'.join(svg + ['</svg>']), encoding='utf-8')


def salvar(caminho, linhas):
    with caminho.open('w', newline='', encoding='utf-8') as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        writer.writeheader()
        writer.writerows(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tamanhos', type=int, nargs='+', default=[1024, 2048, 4096])
    parser.add_argument('--processos', type=int, nargs='+', default=[1, 2, 4, 8])
    parser.add_argument('--passes', type=int, default=30)
    parser.add_argument('--repeticoes', type=int, default=10)
    parser.add_argument('--aquecimentos', type=int, default=1)
    parser.add_argument('--test', action='store_true', help='somente valida casos pequenos e limites')
    args = parser.parse_args()
    if (min(args.tamanhos + args.processos) < 1 or args.passes < 0 or
            args.repeticoes < 1 or args.aquecimentos < 0):
        parser.error('tamanhos/processos/repetições positivos; passes/aquecimentos não negativos')
    subprocess.run(['make', 'baseline', 'mpi'], cwd=RAIZ, check=True)
    baseline = str(RAIZ / 'baseline/convolucao.out')
    mpi = str(RAIZ / 'mpi/convolucao_mpi.out')

    def medir(n, passes, p=None):
        comando = [baseline, str(n), str(passes)] if p is None else [
            'mpirun', '-np', str(p), mpi, str(n), str(passes), '--validate']
        return executar(comando, n, passes, validar=p is not None)

    if args.test:
        # Inclui faixas irregulares, ranks vazios, bordas e paridade dos buffers.
        for n in (1, 2, 3, 5, 8, 17):
            for passes in (0, 1, 2, 3, 6):
                esperado = medir(n, passes)[0]
                for p in args.processos:
                    if medir(n, passes, p)[0] != esperado:
                        raise RuntimeError(f'Checksum divergente: N={n}, passes={passes}, P={p}')
        print('Validação integral e checksum externo: OK')
        return

    medicoes, resumo = [], []
    for n in args.tamanhos:
        for _ in range(args.aquecimentos):
            medir(n, args.passes)
        seriais = [medir(n, args.passes) for _ in range(args.repeticoes)]
        esperado = seriais[0][0]
        if any(r[0] != esperado for r in seriais):
            raise RuntimeError('Baseline inconsistente')
        t1 = statistics.median(r[1] for r in seriais)
        for i, r in enumerate(seriais, 1):
            medicoes.append(dict(implementacao='baseline', n=n, passes=args.passes,
                                 processos=1, repeticao=i, checksum=r[0], tempo_s=r[1],
                                 comunicacao_s=r[2], computacao_s=r[1]))
        for p in args.processos:
            print(f'Medindo MPI: N={n}, passes={args.passes}, processos={p}', flush=True)
            for _ in range(args.aquecimentos):
                medir(n, args.passes, p)
            amostras = []
            for i in range(1, args.repeticoes + 1):
                r = medir(n, args.passes, p)
                if r[0] != esperado:
                    raise RuntimeError(f'Checksum divergente: N={n}, P={p}')
                amostras.append(r)
                medicoes.append(dict(implementacao='mpi', n=n, passes=args.passes,
                                     processos=p, repeticao=i, checksum=r[0], tempo_s=r[1],
                                     comunicacao_s=r[2], computacao_s=r[3]))
            tp = statistics.median(r[1] for r in amostras)
            if tp <= 0:
                raise RuntimeError('Tempo insuficiente; aumente o tamanho/passes')
            resumo.append(dict(n=n, passes=args.passes, processos=p, repeticoes=args.repeticoes,
                               t1_mediana_s=t1, tp_mediana_s=tp,
                               comunicacao_mediana_s=statistics.median(r[2] for r in amostras),
                               computacao_mediana_s=statistics.median(r[3] for r in amostras),
                               speedup=t1/tp, eficiencia=t1/tp/p))
    dados, graficos = RAIZ / 'mpi/dados', RAIZ / 'mpi/graficos'
    dados.mkdir(exist_ok=True)
    graficos.mkdir(exist_ok=True)
    salvar(dados / 'analise_medicoes.csv', medicoes)
    salvar(dados / 'analise_resumo.csv', resumo)
    curva(graficos / 'speedup.svg', resumo, 'speedup', 'Speedup: T baseline / T MPI', lambda p: p)
    curva(graficos / 'eficiencia.svg', resumo, 'eficiencia', 'Eficiência: Speedup / processos', lambda p: 1)
    curva(graficos / 'comunicacao.svg', resumo, 'comunicacao_mediana_s', 'Comunicação (segundos)', lambda p: 0)
    curva(graficos / 'computacao.svg', resumo, 'computacao_mediana_s', 'Computação (segundos)', lambda p: 0)
    print(f'CSVs: {dados}; gráficos SVG: {graficos}')


if __name__ == '__main__':
    main()
