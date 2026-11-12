import re
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

    return subprocess.run(["./baseline/convolucao.out", str(tamanho), str(PASSES)],
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

for n in TAMANHOS_MATRIZ:
    # Loop de Aquecimento: valores descartados
    for _ in range(AQUECIMENTOS):
        resultado = executar_baseline(n)

    # Para este N e este número de passes, a primeira medição define o checksum
    # esperado; todas as demais repetições devem retornar o mesmo valor.
    checksum_esperado = None

    # Loop de Execução final: valores capturados
    for i in range(1, REPETICOES + 1):
        resultado = executar_baseline(n)

        saida_bruta = resultado.stdout.strip()
        formato_esperado = padrao_saida.match(saida_bruta)

        if (formato_esperado is None):
            raise RuntimeError(f"Formato de saída inesperado: {saida_bruta}")

        n_obtido = int(formato_esperado.group(1))
        passes_obtidos = int(formato_esperado.group(2))
        checksum = formato_esperado.group(3)
        tempo_s = float(formato_esperado.group(4))

        if checksum_esperado is None:
            checksum_esperado = checksum

        elif checksum != checksum_esperado:
            raise RuntimeError(
                f"Checksum divergente em N={n}, passes={PASSES}, ",
                f"repetição={i}: esperado {checksum_esperado}")

print("Perfilamento finalizado")
