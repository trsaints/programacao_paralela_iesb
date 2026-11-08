#include <iostream>
#include <vector>
#include <string>
#include <omp.h>
#include "coeficiente_variacao.hpp"

using namespace std;

int main(int argc, char *argv[])
{
    string caminho = (argc > 1) ? argv[1] : "dados.txt";
    vector<CvPessoa> pessoas;

    if (!cv_carregar_dados(caminho, pessoas))
        return 1;

    CvParametros estatura{"Estatura (cm)", {}, 8.0};
    CvParametros peso{"Peso (kg)", {}, 4.0};

    estatura.amostra.reserve(pessoas.size());
    peso.amostra.reserve(pessoas.size());

    for (const auto &pessoa : pessoas)
    {
        estatura.amostra.push_back(pessoa.estatura);
        peso.amostra.push_back(pessoa.peso);
    }

    omp_set_dynamic(0);

    const int repeticoes = 100;
    vector<CvPerfilamento> perfis;
    perfis.reserve(15);

    // Aquecimento serial.
    (void)cv_executar_serial(estatura);
    (void)cv_executar_serial(peso);

    // Aquecimento paralelo para cada tamanho de equipe.
    for (int threads = 2; threads <= 16; ++threads)
    {
        omp_set_num_threads(threads);
        (void)cv_executar_paralelo(estatura);
        (void)cv_executar_paralelo(peso);
    }

    // Mede a referência serial no mesmo dataset.
    CvResultado resultado_estatura_serial;
    CvResultado resultado_peso_serial;

    double inicio = omp_get_wtime();

    for (int i = 0; i < repeticoes; ++i)
    {
        resultado_estatura_serial = cv_executar_serial(estatura);
        resultado_peso_serial = cv_executar_serial(peso);
    }

    const double tempo_serial_us =
        ((omp_get_wtime() - inicio) / repeticoes) * 1'000'000.0;

    // Mede o caminho paralelo para cada quantidade de threads.
    for (int threads = 2; threads <= 16; ++threads)
    {
        omp_set_num_threads(threads);

        int threads_ativas = 0;
#pragma omp parallel
        {
#pragma omp single
            threads_ativas = omp_get_num_threads();
        }

        CvResultado resultado_estatura_paralelo;
        CvResultado resultado_peso_paralelo;

        inicio = omp_get_wtime();

        for (int i = 0; i < repeticoes; ++i)
        {
            resultado_estatura_paralelo = cv_executar_paralelo(estatura);
            resultado_peso_paralelo = cv_executar_paralelo(peso);
        }

        const double tempo_paralelo_us =
            ((omp_get_wtime() - inicio) / repeticoes) * 1'000'000.0;

        const double speedup =
            tempo_paralelo_us > 0.0
                ? tempo_serial_us / tempo_paralelo_us
                : 0.0;

        const double eficiencia_percentual =
            threads_ativas > 0
                ? speedup / threads_ativas * 100.0
                : 0.0;

        CvPerfilamento perfilamento{
            threads,
            threads_ativas,
            tempo_serial_us,
            tempo_paralelo_us,
            speedup,
            eficiencia_percentual,
            resultado_estatura_serial.valor,
            resultado_estatura_paralelo.valor,
            resultado_peso_serial.valor,
            resultado_peso_paralelo.valor};

        perfis.push_back(perfilamento);
    }

    cv_exibir_comparativo(caminho, pessoas.size(), perfis);

    return 0;
}