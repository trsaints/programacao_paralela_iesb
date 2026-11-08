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
    const int threads_configuradas = omp_get_max_threads();
    const int repeticoes = 100;

    // Aquecimento: descarta os resultados e não inclui esta execução na medição.
    (void)cv_executar_serial(estatura);
    (void)cv_executar_serial(peso);
    (void)cv_executar_paralelo(estatura);
    (void)cv_executar_paralelo(peso);

    CvResultado resultado_estatura_serial;
    CvResultado resultado_peso_serial;

    double inicio = omp_get_wtime();

    for (int i = 0; i < repeticoes; ++i)
    {
        resultado_estatura_serial = cv_executar_serial(estatura);
        resultado_peso_serial = cv_executar_serial(peso);
    }

    const double t1 = (omp_get_wtime() - inicio) / repeticoes;

    CvResultado resultado_estatura_paralelo;
    CvResultado resultado_peso_paralelo;

    inicio = omp_get_wtime();

    for (int i = 0; i < repeticoes; ++i)
    {
        resultado_estatura_paralelo = cv_executar_paralelo(estatura);
        resultado_peso_paralelo = cv_executar_paralelo(peso);
    }

    const double tp = (omp_get_wtime() - inicio) / repeticoes;

    // Exibição fica fora da medição.
    cout << "\nResultados seriais\n";
    cv_exibir_resultado(estatura, resultado_estatura_serial);
    cv_exibir_resultado(peso, resultado_peso_serial);

    cout << "\nResultados paralelos\n";
    cv_exibir_resultado(estatura, resultado_estatura_paralelo);
    cv_exibir_resultado(peso, resultado_peso_paralelo);

    const double speedup = t1 / tp;
    const double eficiencia = speedup / threads_configuradas;

    cout << fixed;
    cout << "\nThreads configuradas: " << threads_configuradas << '\n';
    cout << "Tempo serial médio: " << t1 << " s\n";
    cout << "Tempo paralelo médio: " << tp << " s\n";
    cout << "Speedup: " << speedup << "x\n";
    cout << "Eficiência: " << eficiencia * 100.0 << "%\n";

    return 0;
}