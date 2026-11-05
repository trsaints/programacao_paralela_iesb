#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>
#include <iomanip>

struct Pessoa
{
    double estatura;
    double peso;
};

struct IntervaloClasse
{
    double lim_inferior;
    double lim_superior;
    double ponto_medio_xi;
    int frequencia_fi;
};

void cv_executar_serial(const std::vector<double> &amostra, double h, const std::string &nome_variavel)
{
    int n = amostra.size();

    if (n == 0)
    {
        std::cerr << "Erro: amostra vazia para " << nome_variavel << std::endl;

        return;
    }

    double valor_min = amostra[0];
    double valor_max = amostra[0];

    for (int i = 1; i < n; i++)
    {
        if (amostra[i] < valor_min)
            valor_min = amostra[i];
        if (amostra[i] > valor_max)
            valor_max = amostra[i];
    }

    // Construção da tabela de classes
    std::vector<IntervaloClasse> tabela_intervalos;
    double cursor = valor_min;

    while (cursor < valor_max)
    {
        IntervaloClasse intervalo;

        intervalo.lim_inferior = cursor;
        intervalo.lim_superior = cursor + h;
        intervalo.ponto_medio_xi = (intervalo.lim_inferior + intervalo.lim_superior) / 2.0;
        intervalo.frequencia_fi = 0;

        tabela_intervalos.push_back(intervalo);

        cursor += h;
    }

    int k_classes = tabela_intervalos.size();

    // Tabulação das frequências via Mapeamento Direto - O(1)
    for (int i = 0; i < n; i++)
    {
        int idx = (int)((amostra[i] - valor_min) / h);

        if (idx >= k_classes)
            idx = k_classes - 1; // Clamp para não exceder valor_max

        tabela_intervalos[idx].frequencia_fi++;
    }

    // Média Ponderada Populacional (mu)
    double soma_ponderada = 0.0;

    for (int i = 0; i < k_classes; i++)
    {
        soma_ponderada += tabela_intervalos[i].ponto_medio_xi * tabela_intervalos[i].frequencia_fi;
    }

    double media_ponderada_mu = soma_ponderada / n;

    // Desvio Padrão Populacional (sigma)
    double soma_desvios_quad = 0.0;

    for (int i = 0; i < k_classes; i++)
    {
        double diferenca = tabela_intervalos[i].ponto_medio_xi - media_ponderada_mu;
        soma_desvios_quad += tabela_intervalos[i].frequencia_fi * pow(diferenca, 2);
    }

    double desvio_padrao_sigma = sqrt(soma_desvios_quad / n);

    // Coeficiente de Variação (CV)
    double cv = (desvio_padrao_sigma / media_ponderada_mu) * 100.00;
}

void cv_exibir_resultados(
    const std::string &nome_variavel,
    double valor_min,
    double valor_max,
    double h,
    int k_classes,
    double media_ponderada_mu,
    double desvio_padrao_sigma,
    double cv,
    const std::vector<IntervaloClasse> &tabela_intervalos)
{
    // Resultados
    std::cout << "\n---------------------------------------------------------" << std::endl;
    std::cout << "Variável Analisada: " << nome_variavel << std::endl;
    std::cout << "Mínimo: " << valor_min << " | Máximo: " << valor_max << std::endl;
    std::cout << "Amplitude de Classe (h): " << h << std::endl;
    std::cout << "Total de Classes (k): " << k_classes << std::endl;
    std::cout << std::fixed << std::setprecision(4);

    std::cout << "Média Ponderada (mu): " << media_ponderada_mu << std::endl;
    std::cout << "Desvio Padrão (sigma): " << desvio_padrao_sigma << std::endl;
    std::cout << "Coeficiente de Variação (CV): " << cv << "%" << std::endl;
    std::cout << "---------------------------------------------------------" << std::endl;

    // Classes
    std::cout << "Distribuição de Frequências: " << std::endl;
    std::cout << "Classe\t[Limite Inferior, Limite Superior)\tPonto Médio (xi)\tFrequência (fi)" << std::endl;

    for (int i = 0; i < k_classes; i++)
    {
        std::cout << i << "\t[" << std::setw(8) << tabela_intervalos[i].lim_inferior
                  << ", " << std::setw(8) << tabela_intervalos[i].lim_superior << ")\t"
                  << std::setw(12) << tabela_intervalos[i].ponto_medio_xi << "\t\t"
                  << std::setw(8) << tabela_intervalos[i].frequencia_fi << std::endl;
    }
}