#include <iostream>
#include <vector>
#include <fstream>
#include <iomanip>
#include <omp.h>
#include "coeficiente_variacao.hpp"

using namespace std;

int main(int argc, char *argv[])
{
    string caminho = (argc > 1) ? argv[1] : "dados.txt";
    vector<CvPessoa> pessoas;

    if (!cv_carregar_dados(caminho, pessoas))
        return 1;

    int total = pessoas.size();

    cout << ">>> Base de dados carregada: " << total << " pessoas. <<<\n"
         << endl;

    vector<double> estaturas;
    vector<double> pesos;

    estaturas.reserve(total);
    pesos.reserve(total);

    for (const auto &p : pessoas)
    {
        estaturas.push_back(p.estatura);
        pesos.push_back(p.peso);
    }

    // Execução Sequencial (TI)
    cout << "\n+--------------------------------------------+" << endl;
    cout << "|\tINICIANDO PROCESSAMENTO SERIAL (T1)\t|" << endl;
    cout << "\n+---------------------------------------------+" << endl;

    double t1_inicio = omp_get_wtime();

    cv_executar_serial(estaturas, 8.0, "Estatura (cm)");
    cv_executar_serial(pesos, 4.0, "Peso (kg)");

    double t1_fim = omp_get_wtime();
    double t1 = t1_fim - t1_inicio;

    // Execução Paralelizada (Tp)
    cout << "\n+--------------------------------------------+" << endl;
    cout << "|\tINICIANDO PROCESSAMENTO PARALELO (Tp)\t|" << endl;
    cout << "\n+---------------------------------------------+" << endl;

    int num_threads = omp_get_max_threads();
    cout << "Threads OpenMP alocadas: " << num_threads << endl;

    double tp_inicio = omp_get_wtime();

    cv_executar_paralelo(estaturas, 8.0, "Estatura (cm)");
    cv_executar_paralelo(pesos, 4.0, "Peso (kg)");

    double tp_fim = omp_get_wtime();
    double tp = tp_fim - tp_inicio;

    // Relatório
    double speedup = t1 / tp;
    double eficiencia = speedup / num_threads;

    cout << "\n+--------------------------------------------+" << endl;
    cout << "|\tMÉTRICAS DE DESEMPENHO\t|" << endl;
    cout << "\n+---------------------------------------------+" << endl;

    cout << fixed << setprecision(6);
    cout << "Tempo Sequencial (T1): " << t1 << " s (" << t1 * 1000.0 << " ms)" << endl;
    cout << "Tempo Paralelo (Tp): " << tp << " s (" << tp * 1000.0 << " ms)" << endl;
    cout << "Speedup (S = T1 / Tp): " << speedup << "x" << endl;
    cout << "Eficiência (E = S / p): " << eficiencia * 100.00 << "%" << endl;
    cout << "\n+---------------------------------------------+" << endl;

    return 0;
}