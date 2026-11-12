# Atividade 09: Desafio OpenMP

O projeto encontra-se no diretório `desafios/coeficiente_variacao/`. 
Para executá-lo, há duas opções:
- **VSCode (somente testes)**: Pressione `F5` e aguarda a compilação + execução do código; ATENÇÃO! Este modo de execução aplica baixa otimização para facilitar a detecção de símbolos pelo depurador VSCode. Não use-a como métrica final, nem assuma que seus valores de referência estejam corretos.
- **Terminal (versão final e otimizada)**:
    1. Compile o código com `g++ -fopenmp -O2 desafios/coeficiente_variacao/main.cpp desafios/coeficiente_variacao/coeficiente_variacao.cpp -o desafios/coeficiente_variacao/main.out`;
    2. Execute o programa com `desafios/coeficiente_variacao/main.out`;

> [!NOTE]
> As instruções de compilação assumem que seu diretório atual (cwd) é a raíz do repositório.