#ifndef COEFICIENTE_VARIACAO_HPP
#define COEFICIENTE_VARIACAO_HPP

#include <iostream>
#include <vector>
#include <fstream>
#include <string>
#include <iomanip>
using namespace std;

/// @brief Representação de uma pessoa, para fins de classificação.
struct CvPessoa
{
    /// @brief Estatura em centímetros (cm).
    double estatura{};

    /// @brief Peso em quilogramas (Kg).
    double peso{};
};

/// @brief Representa cada um dos intevalos de frequência agrupada (faixas estatísticas).
struct CvClasse
{
    /// @brief Define a fronteira mínima para a classificação de pessoas.
    double lim_inferior{};

    /// @brief Define a fronteira máxima para a classificação de pessoas. Este desafio delimita o valor para `limite_inf + 8.0`, se usado em altura (cm), ou `limite_inf + 4.0`, se usado em peso (kg).
    double lim_superior{};

    /// @brief Representa `xi`: a média aritmética entre o limite inferior e o limite superior da classe. A estatística adota este valor como representativo único de todas as Pessoas em uma determinado InvervaloClasse.
    double ponto_medio{};

    /// @brief  Representa `fi`: a quantidade de Pessoas cujos valores caíram dentro da classe em questão, atuando como peso de ponderação da classe.
    int frequencia{};
};

/// @brief Conjunto de dados e metadados para execução do cálculo de Coeficiente de Variação
struct CvParametros
{
    /// @brief Rótulo de atributo para calcular o CV, para fins de identificação e exibição.
    string rotulo{};

    /// @brief O conjunto de dados.
    vector<double> amostra{};

    /// @brief Representa a amplitude (h) a ser aplicada na segregação de classes de dados.
    double amplitude{};
};

/// @brief Representa conjunto de dados obtidos após a execução do cálculo de Coeficiente de Variação.
struct CvResultado
{
    /// @brief As classes obtidas a partir do conjunto de dados.
    vector<CvClasse> classes;

    /// @brief O menor valor do conjunto de dados fornecido.
    double valor_min{};

    /// @brief O maior valor do conjunto de dados fornecido.
    double valor_max{};

    /// @brief A média ponderada do conjunto de dados fornecido.
    double media{};

    /// @brief O desvio padrão do conjunto de dados fornecido.
    double desvio{};

    /// @brief O valor final do Coeficiente de Variação, obtido a partir do conjunto de dados.
    double valor{};
};

/**
 * Carrega um dataset para classificação de um arquivo de dados .txt.
 * @param caminho_arquivo O caminho relativo até o arquivo bruto de dados.
 * @param pessoas Conjunto de CvPessoa a ser materializado a partir do arquivo bruto de dados.
 */
bool cv_carregar_dados(const string &caminho_arquivo, vector<CvPessoa> &pessoas);

/// @brief Realiza a exibição do cálculo de Coeficiente de variação
void cv_exibir_resultado(const CvParametros &parametros, const CvResultado &resultado);

/// @brief Calcula o Coeficiente de Variação (CV) de uma amostra de dados, de maneira sequencial.
CvResultado cv_executar_serial(const CvParametros &parametros);

/// @brief Calcula o Coeficiente de Variação (CV) de uma amostra de dados, de maneira paralelizada (via OpenMP).
CvResultado cv_executar_paralelo(const CvParametros &parametros);

#endif // COEFICIENTE_VARIACAO_HPP