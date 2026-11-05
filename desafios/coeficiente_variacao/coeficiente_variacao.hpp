#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>
#include <string>
#include <iomanip>
#include <chrono>
#include <cstdlib>

/**
 * Representação de uma pessoa.
 */
struct CvPessoa
{
    /**
     * Estatura em cm.
     */
    double estatura;
    /**
     * Peso em Kg.
     */
    double peso;
};

/**
 * Representa cada um dos intevalos de frequência agrupada (faixas estatísticas).
 */
struct CvIntervaloClasse
{
    /**
     * Define a fronteira mínima para a classificação de pessoas.
     */
    double lim_inferior;
    /**
     * Define a fronteira máxima para a classificação de pessoas. Este desafio delimita o valor para `limite_inf + 8.0`, se usado em altura (cm), ou `limite_inf + 4.0`, se usado em peso (kg).
     */
    double lim_superior;
    /**
     * Medida aritmética entre o limite inferior e o limite superior da classe. A estatística adota este valor como representativo único de todas as Pessoas em uma determinado InvervaloClasse.
     */
    double ponto_medio_xi;

    /**
     * Quantidade de Pessoas cujos valores caíram dentro do intervalo de IntervaloClasse em questão, atuando como peso de ponderação da Classe.
     */
    int frequencia_fi;
};

/**
 * Calcula o Coeficiente de Variação (CV) de uma amostra de dados, de maneira sequencial.
 * @param amostra o conjunto de dados para executar a classificação
 * @param h a amplitude de `amostra`
 * @param rotulo_atributo o rótulo para descrever o conjunto de dados
 */
void cv_executar_serial(const std::vector<double> &amostra, double h, const std::string &rotulo_atributo);

/**
 * Realiza a exibição do cálculo de Coeficiente de variação
 */
void cv_exibir_resultados(
    const std::string &nome_variavel,
    double valor_min,
    double valor_max,
    double h,
    int k_classes,
    double media_ponderada_mu,
    double desvio_padrao_sigma,
    double cv,
    const std::vector<CvIntervaloClasse> &tabela_intervalos);