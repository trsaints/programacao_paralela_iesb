#include <iostream>
#include <vector>
#include <fstream>
#include <chrono>
#include <iomanip>
#include "coeficiente_variacao.hpp"

int main(int argc, char *argv[])
{
    std::string nome_arquivo = "dados.txt";

    if (argc > 1)
    {
        nome_arquivo = argv[1];
    }

    std::ifstream arquivo(nome_arquivo);

    if (!arquivo.is_open())
    {
        std::cerr << "Falha ao abrir o arquivo: " << nome_arquivo << std::endl;

        return 1;
    }

    std::vector<double> estaturas;
    std::vector<double> pesos;

    estaturas.reserve(1000);
    pesos.reserve(1000);

    double estatura_tmp, peso_tmp;

    while (arquivo >> estatura_tmp >> peso_tmp)
    {
        estaturas.push_back(estatura_tmp);
        pesos.push_back(peso_tmp);
    }

    arquivo.close();

    std::cout << "EXECUÇÃO SEQUENCIAL (BASELINE - T1)" << std::endl;
    std::cout << "TOTAL DE AMOSTRAS: " << estaturas.size() << std::endl;

    auto t_inicio = std::chrono::high_resolution_clock::now();

    cv_executar_serial(estaturas, 8.0, "Estatura (cm)");
    cv_executar_serial(pesos, 4.0, "Peso (Kg)");

    auto t_fim = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> tempo_ms = t_fim - t_inicio;

    std::cout << "\n>>> Tempo Total Sequencial (T1): "
              << tempo_ms.count() << " ms ("
              << (tempo_ms.count() / 1000.0) << " s) <<<" << std::endl;

    return 0;
}