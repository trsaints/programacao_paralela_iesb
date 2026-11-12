import csv
import re
import statistics
import subprocess

TAMANHOS_MATRIZ = [1024, 2048, 4096]
PASSES = 30
AQUECIMENTOS = 1
REPETICOES = 10


def executar_baseline(tamanho: int):
    """
    Executa o programa do algoritmo de baseline sequencial.

    Args:
        tamamho (int): Tamanho da matriz a ser processada.

    Returns:
        s: Uma instância `CompletedProcess[str]`, contendo a saída do algoritmo.
    """
    if tamanho not in TAMANHOS_MATRIZ:
        raise ValueError(
            f"Valor {tamanho} não está presente na faixa de tamanhos {TAMANHOS_MATRIZ}")

    return subprocess.run(
        ["./baseline/convolucao.out", str(tamanho), str(PASSES)],
        capture_output=True,
        text=True,
        check=True)


# Compilar
subprocess.run(
    ["g++", "-O2", "-o", "baseline/convolucao.out",  "baseline/04_convolucao.cpp"],
    check=True)

# Formato de saída do programa. Ex.: N=1 passes=30 checksum=100 tempo=10s
padrao_saida = re.compile(
    r"N=(\d+)\s+passes=(\d+)\s+checksum=([0-9.+-]+)\s+tempo=([0-9.+-]+)\s+s")

with open(
    "dados/baseline_medicoes.csv", mode="w", newline="", encoding="utf-8",
) as arquivo_medicoes, open(
    "dados/baseline_resumo.csv", mode="w", newline="", encoding="utf-8",
) as arquivo_estatisticas:
    colunas_medicoes = [
        "implementacao",
        "n",
        "passes",
        "repeticao",
        "checksum",
        "tempo_s",
    ]

    colunas_estatisticas = [
        "implementacao",
        "n",
        "passes",
        "repeticoes",
        "checksum",
        "tempo_medio_s",
        "tempo_mediano_s",
        "desvio_padrao_s",
    ]

    medicoes_writer = csv.DictWriter(
        arquivo_medicoes, fieldnames=colunas_medicoes)
    medicoes_writer.writeheader()

    estatisticas_writer = csv.DictWriter(
        arquivo_estatisticas, fieldnames=colunas_estatisticas)
    estatisticas_writer.writeheader()

    for n in TAMANHOS_MATRIZ:
        print(f"Executando perfilamento para N={n}")

# Loop de Aquecimento: valores descartados
        for _ in range(AQUECIMENTOS):
            resultado = executar_baseline(n)

        # Para este N e este número de passes, a primeira medição define o checksum
        # esperado; todas as demais repetições devem retornar o mesmo valor.
        checksum_esperado = None
        tempos_n: list[float] = []

# Loop de Execução final: valores capturados
        for i in range(1, REPETICOES + 1):
            resultado = executar_baseline(n)

            saida_bruta = resultado.stdout.strip()
            formato_esperado = padrao_saida.match(saida_bruta)

            if (formato_esperado is None):
                raise RuntimeError(
                    f"Formato de saída inesperado: {saida_bruta}")

            n_obtido = int(formato_esperado.group(1))
            passes_obtidos = int(formato_esperado.group(2))

            if n_obtido != n or passes_obtidos != PASSES:
                raise RuntimeError(
                    f"Parâmetros retornados inesperados: N={n_obtido}, passes={passes_obtidos}")

            checksum_obtido = formato_esperado.group(3)

            tempo_s = float(formato_esperado.group(4))
            tempos_n.append(tempo_s)

            if checksum_esperado is None:
                checksum_esperado = checksum_obtido

            elif checksum_obtido != checksum_esperado:
                raise RuntimeError(
                    f"Checksum divergente em N={n}, passes={PASSES}, "
                    f"repetição={i}: esperado {checksum_esperado}, obtido {checksum_obtido}")

            medicoes_writer.writerow({
                "implementacao": "baseline",
                "n": n,
                "passes": PASSES,
                "repeticao": i,
                "checksum": checksum_obtido,
                "tempo_s": tempo_s
            })

# Estatísticas das iterações de N
        estatisticas_writer.writerow({
            "implementacao": "baseline",
            "n": n,
            "passes": PASSES,
            "repeticoes": REPETICOES,
            "checksum": checksum_esperado,
            "tempo_medio_s": statistics.mean(tempos_n),
            "tempo_mediano_s": statistics.median(tempos_n),
            "desvio_padrao_s": statistics.stdev(tempos_n)
        })

print("Perfilamento finalizado e disponível em 'dados/baseline_medicoes.csv'.\n"
      "Estatísticas disponíveis em 'dados/baseline_resumo.csv'.")
