#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>
#include <iomanip>
#include "coeficiente_variacao.hpp"

using namespace std;

bool cv_carregar_dados(const string &caminho_arquivo, vector<CvPessoa> &pessoas)
{
    ifstream arquivo(caminho_arquivo);

    if (!arquivo.is_open())
    {
        cerr << "Erro ao abrir o arquivo: " << caminho_arquivo << endl;

        return false;
    }

    pessoas.clear();
    pessoas.reserve(1000);

    CvPessoa p;

    while (arquivo >> p.estatura >> p.peso)
    {
        pessoas.push_back(p);
    }

    arquivo.close();

    return !pessoas.empty();
}

void cv_exibir_resultado(const CvParametros &parametros, const CvResultado &resultado)
{
    int k = resultado.classes.size();

    // Resultados
    cout << "\n---------------------------------------------------------" << endl;
    cout << "Variável Analisada: " << parametros.rotulo << endl;
    cout << "Mínimo: " << resultado.valor_min << " | Máximo: " << resultado.valor_max << endl;
    cout << "Amplitude de Classe (h): " << parametros.amplitude << endl;
    cout << "Total de Classes (k): " << k << endl;
    cout << fixed << setprecision(4);

    cout << "Média Ponderada (mu): " << resultado.media << endl;
    cout << "Desvio Padrão (sigma): " << resultado.desvio << endl;
    cout << "Coeficiente de Variação (CV): " << resultado.valor << "%" << endl;
    cout << "---------------------------------------------------------" << endl;

    // Classes
    cout << "Distribuição de Frequências: " << endl;
    cout << left
         << setw(8) << "Classe" << " | "
         << setw(20) << "Intervalo" << " | "
         << setw(18) << "Ponto medio (xi)" << " | "
         << right << setw(15) << "Frequencia (fi)" << '\n';

    for (int i = 0; i < k; i++)
    {
        const auto &classe = resultado.classes[i];

        cout << left << setw(8) << i << " | ["
             << right << setw(8) << classe.lim_inferior << ", "
             << setw(8) << classe.lim_superior << ") | "
             << setw(18) << classe.ponto_medio << " | "
             << setw(15) << classe.frequencia << '\n';
    }
}

CvResultado cv_executar_serial(const CvParametros &parametros)
{
    int n_amostras = parametros.amostra.size();

    if (n_amostras == 0)
    {
        cerr << "Erro: amostra vazia para " << parametros.rotulo << endl;

        CvResultado r0;

        return r0;
    }

    CvResultado resultado;
    resultado.valor_min = parametros.amostra[0];
    resultado.valor_max = parametros.amostra[0];

    for (int i = 1; i < n_amostras; i++)
    {
        if (parametros.amostra[i] < resultado.valor_min)
            resultado.valor_min = parametros.amostra[i];

        if (parametros.amostra[i] > resultado.valor_max)
            resultado.valor_max = parametros.amostra[i];
    }

    // Construção da tabela de classes
    double cursor = resultado.valor_min;

    while (cursor < resultado.valor_max)
    {
        CvClasse classe;

        classe.lim_inferior = cursor;
        classe.lim_superior = cursor + parametros.amplitude;
        classe.ponto_medio = (classe.lim_inferior + classe.lim_superior) / 2.0;
        classe.frequencia = 0;

        resultado.classes.push_back(classe);

        cursor += parametros.amplitude;
    }

    int k_classes = resultado.classes.size();

    // Tabulação das frequências via Mapeamento Direto - O(1)
    for (int i = 0; i < n_amostras; i++)
    {
        int idx = (int)((parametros.amostra[i] - resultado.valor_min) / parametros.amplitude);

        if (idx >= k_classes)
            idx = k_classes - 1; // Clamp para não exceder valor_max

        resultado.classes[idx].frequencia++;
    }

    // Média Ponderada Populacional (mu)
    double soma_ponderada = 0.0;

    for (int i = 0; i < k_classes; i++)
    {
        soma_ponderada += resultado.classes[i].ponto_medio * resultado.classes[i].frequencia;
    }

    resultado.media = soma_ponderada / n_amostras;

    // Desvio Padrão Populacional (sigma)
    double soma_desvios_quad = 0.0;

    for (int i = 0; i < k_classes; i++)
    {
        double diferenca = resultado.classes[i].ponto_medio - resultado.media;
        soma_desvios_quad += resultado.classes[i].frequencia * pow(diferenca, 2);
    }

    resultado.desvio = sqrt(soma_desvios_quad / n_amostras);
    resultado.valor = (resultado.desvio / resultado.media) * 100.00;

    return resultado;
}

CvResultado cv_executar_paralelo(const CvParametros &parametros)
{
    int n_amostras = parametros.amostra.size();

    if (n_amostras == 0)
    {
        cerr << "Erro: amostra vazia para " << parametros.rotulo << endl;

        CvResultado r0;

        return r0;
    }

    CvResultado resultado;
    resultado.valor_min = parametros.amostra[0];
    resultado.valor_max = parametros.amostra[0];

    for (int i = 1; i < n_amostras; i++)
    {
        if (parametros.amostra[i] < resultado.valor_min)
            resultado.valor_min = parametros.amostra[i];

        if (parametros.amostra[i] > resultado.valor_max)
            resultado.valor_max = parametros.amostra[i];
    }

    double cursor = resultado.valor_min;

    while (cursor < resultado.valor_max)
    {
        CvClasse classe;

        classe.lim_inferior = cursor;
        classe.lim_superior = cursor + parametros.amplitude;
        classe.ponto_medio = (classe.lim_inferior + classe.lim_superior) / 2.0;
        classe.frequencia = 0;

        resultado.classes.push_back(classe);

        cursor += parametros.amplitude;
    }

    int k_classes = resultado.classes.size();

// Contagem Parelela com Histograma Local (evita race condition)
#pragma omp parallel
    {
        vector<int> frequencia_local(k_classes, 0);

#pragma omp for schedule(static) nowait
        for (int i = 0; i < n_amostras; i++)
        {
            int idx = (int)((parametros.amostra[i] - resultado.valor_min) / parametros.amplitude);

            if (idx >= k_classes)
                idx = k_classes - 1;

            frequencia_local[idx]++;
        }

        for (int c = 0; c < k_classes; c++)
        {
#pragma omp atomic
            resultado.classes[c].frequencia += frequencia_local[c];
        }
    }

    // Média Ponderada paralela
    double soma_ponderada = 0.0;

#pragma omp parallel for reduction(+ : soma_ponderada) schedule(static)
    for (int i = 0; i < k_classes; i++)
    {
        soma_ponderada += resultado.classes[i].ponto_medio * resultado.classes[i].frequencia;
    }

    resultado.media = soma_ponderada / n_amostras;

    // Desvio Padrão paralelo
    double soma_desvios_quad = 0.0;

#pragma omp parallel for reduction(+ : soma_desvios_quad) schedule(static)
    for (int i = 0; i < k_classes; i++)
    {
        double diferenca = resultado.classes[i].ponto_medio - resultado.media;
        soma_desvios_quad += resultado.classes[i].frequencia * pow(diferenca, 2);
    }

    resultado.desvio = sqrt(soma_desvios_quad / n_amostras);
    resultado.valor = (resultado.desvio / resultado.media) * 100.0;

    return resultado;
}