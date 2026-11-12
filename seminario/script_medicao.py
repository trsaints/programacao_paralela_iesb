import re
import subprocess

TAMANHOS_MATRIZ = [1024, 2048, 4096]
PASSES = 30
AQUECIMENTOS = 1
REPETICOES = 10

# Compilar
subprocess.run(
    ["g++", "-O2", "-o", "baseline/convolucao.out",  "baseline/04_convolucao.cpp"],
    check=True)

# Formato de saída do programa. Ex.: N=1 passes=30 checksum=100 tempo=
padrao_saida = re.compile(
    r"N=(\d+)\s+passes=(\d+)\s+checksum=([0-9.+-]+)\s+tempo=([0-9.+-]+)\s+s")

for n in range(1, 11):
    # Executar o programa
    resultado = subprocess.run(["./baseline/convolucao.out", str(n), str(PASSES)],
                               capture_output=True,
                               text=True,
                               check=True)

    if n == 1:
        continue  # impede o warm-up de ser impresso no stdout e ser incluso no csv de profile

    saida_bruta = resultado.stdout.strip()
    formato_esperado = padrao_saida.match(saida_bruta)

    if (formato_esperado is None):
        raise RuntimeError(f"Formato de saída inesperado: {saida_bruta}")

    n_obtido = int(formato_esperado.group(1))
    passes_obtidos = int(formato_esperado.group(2))
    checksum = formato_esperado.group(3)
    tempo_s = float(formato_esperado.group(4))

print("Perfilamento finalizado")