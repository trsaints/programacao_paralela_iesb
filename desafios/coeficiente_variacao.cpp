#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>
#include <algorithm>
#include <chrono>

/**
 * Representação de uma pessoa.
 */
struct Pessoa
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
struct Classe
{
    /**
     * Define a fronteira mínima para a classificação de pessoas.
     */
    double limite_inf;
    /**
     * Define a fronteira máxima para a classificação de pessoas. Este desafio delimita o valor para `limite_inf + 8.0`, se usado em altura (cm), ou `limite_inf + 4.0`, se usado em peso (kg).
     */
    double limite_sup;
    /**
     * Medida aritmética entre o limite inferior e o limite superior da classe. A estatística adota este valor como representativo único de todas as Pessoas em uma determinada Classe.
     */
    double ponto_medio;

    /**
     * Quantidade de Pessoas cujos valores caíram dentro do intervalo de Classe em questão, atuando como peso de ponderação da Classe.
     */
    int frequencia;
};
