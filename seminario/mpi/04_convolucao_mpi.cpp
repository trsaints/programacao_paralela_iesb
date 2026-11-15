// Faixas horizontais, halos de uma linha e reconstrução no rank 0.
// Usamos a API C; evita carregar os bindings C++ legados do OpenMPI.
#define OMPI_SKIP_MPICXX 1
#include <mpi.h>
#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static bool inteiro(const char* texto, int minimo, int& valor) {
    char* fim = nullptr;
    errno = 0;
    long v = std::strtol(texto, &fim, 10);
    if (errno || fim == texto || *fim || v < minimo || v > INT_MAX) return false;
    valor = static_cast<int>(v);
    return true;
}

static std::vector<float> entrada(int n) {
    std::vector<float> a(static_cast<size_t>(n) * n);
    for (size_t i = 0; i < a.size(); ++i)
        a[i] = static_cast<float>((i * 131) % 256);
    return a;
}

// Mesma ordem de operações e mesmas bordas dos dois buffers do baseline.
static std::vector<float> referencia(int n, int passes) {
    auto a = entrada(n);
    std::vector<float> b(a.size(), 0.0f);
    for (int p = 0; p < passes; ++p) {
        for (int y = 1; y < n - 1; ++y)
            for (int x = 1; x < n - 1; ++x) {
                float s = 0;
                for (int dy = -1; dy <= 1; ++dy)
                    for (int dx = -1; dx <= 1; ++dx)
                        s += a[(y + dy) * n + x + dx];
                b[y * n + x] = s / 9.0f;
            }
        a.swap(b);
    }
    return a;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, processos;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &processos);
    int n = 2000, passes = 30;
    bool validar = argc == 4 && std::strcmp(argv[3], "--validate") == 0;
    if (argc > 4 || (argc == 4 && !validar) ||
        (argc > 1 && !inteiro(argv[1], 1, n)) ||
        (argc > 2 && !inteiro(argv[2], 0, passes)) ||
        static_cast<long long>(n) * n > INT_MAX) {
        if (rank == 0) std::fprintf(stderr, "Uso: %s N>=1 PASSES>=0 [--validate]; N*N <= INT_MAX\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    std::vector<int> contagens(processos), deslocamentos(processos);
    for (int r = 0, inicio = 0; r < processos; ++r) {
        int linhas = n / processos + (r < n % processos ? 1 : 0);
        contagens[r] = linhas * n;
        deslocamentos[r] = inicio * n;
        inicio += linhas;
    }
    int linhas = contagens[rank] / n;
    int inicio = deslocamentos[rank] / n;
    int ativos = std::min(n, processos);
    int acima = rank > 0 && linhas ? rank - 1 : MPI_PROC_NULL;
    int abaixo = rank + 1 < ativos && linhas ? rank + 1 : MPI_PROC_NULL;
    std::vector<float> a((static_cast<size_t>(linhas) + 2) * n, 0.0f), b(a.size(), 0.0f);
    std::vector<float> global;
    if (rank == 0) global = entrada(n);

    double comunicacao = 0, computacao = 0;
    MPI_Barrier(MPI_COMM_WORLD);
    double total_inicio = MPI_Wtime(), t = MPI_Wtime();
    MPI_Scatterv(rank == 0 ? global.data() : nullptr, contagens.data(),
                 deslocamentos.data(), MPI_FLOAT, a.data() + n,
                 contagens[rank], MPI_FLOAT, 0, MPI_COMM_WORLD);
    comunicacao += MPI_Wtime() - t;
    for (int p = 0; p < passes; ++p) {
        if (linhas) {
            t = MPI_Wtime();
            MPI_Sendrecv(a.data() + n, n, MPI_FLOAT, acima, 0,
                         a.data() + (static_cast<size_t>(linhas) + 1) * n,
                         n, MPI_FLOAT, abaixo, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            MPI_Sendrecv(a.data() + static_cast<size_t>(linhas) * n,
                         n, MPI_FLOAT, abaixo, 1, a.data(), n, MPI_FLOAT,
                         acima, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            comunicacao += MPI_Wtime() - t;
            t = MPI_Wtime();
            for (int y = 1; y <= linhas; ++y) {
                int global_y = inicio + y - 1;
                if (global_y == 0 || global_y == n - 1) continue;
                for (int x = 1; x < n - 1; ++x) {
                    float s = 0;
                    for (int dy = -1; dy <= 1; ++dy)
                        for (int dx = -1; dx <= 1; ++dx)
                            s += a[static_cast<size_t>(y + dy) * n + x + dx];
                    b[static_cast<size_t>(y) * n + x] = s / 9.0f;
                }
            }
            a.swap(b);
            computacao += MPI_Wtime() - t;
        }
    }
    t = MPI_Wtime();
    MPI_Gatherv(a.data() + n, contagens[rank], MPI_FLOAT,
                rank == 0 ? global.data() : nullptr, contagens.data(),
                deslocamentos.data(), MPI_FLOAT, 0, MPI_COMM_WORLD);
    comunicacao += MPI_Wtime() - t;
    double locais[] = {MPI_Wtime() - total_inicio, comunicacao, computacao};
    double maximos[3];
    MPI_Reduce(locais, maximos, 3, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    int sucesso = 1;
    if (rank == 0) {
        if (validar) {
            auto esperado = referencia(n, passes);
            sucesso = std::memcmp(global.data(), esperado.data(), global.size() * sizeof(float)) == 0;
            std::fprintf(stderr, "validacao=%s\n", sucesso ? "OK" : "FALHOU");
        }
        double soma = 0;
        for (float v : global) soma += v;
        std::printf("N=%d passes=%d  checksum=%.2f  tempo=%.9f s\n", n, passes, soma, maximos[0]);
        std::fprintf(stderr, "comunicacao_s=%.9f computacao_s=%.9f\n", maximos[1], maximos[2]);
    }
    MPI_Bcast(&sucesso, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return sucesso ? 0 : 2;
}
