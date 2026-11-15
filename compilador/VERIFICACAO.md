# Verificação — 15/11/2026

16 testes próprios aprovados. Também aprovados os testes dos módulos afetados: Organizador (38), Digitalizador/pipeline (7) e Emissor (11). Captador não foi alterado nesta entrega.

O conjunto sintético de 500 questões, organizado em 50 famílias distintas de dez textos, possui 124.750 pares possíveis. O modo padrão calculou 2.250 e recuperou os 50 grupos esperados. Isso verifica a implementação nesse conjunto controlado; não mede precisão/recall em questões jurídicas reais. Há teste separado para A~B, B~C e A não semelhante a C: não cria grupo de três membros.

Comandos comparar, similares, analisar e consultar foram exercitados. Verificados snapshot de mais de 100 questões sem perdas de paginação, falhas/bloqueios de escrita, preservação integral da base, integridade de resultados arquivados, nulidade de dimensões desconhecidas e reprodutibilidade entre processos com seeds diferentes de hash.

Na base real de teste ENAM 2026.1 (80 questões): 3.160 pares possíveis, 1.565 comparados pelo índice padrão, nenhum retido acima do limiar 60 e nenhum grupo acima de 80. Preservadas 80 referências de ocorrência e uma ficha de prova. O resultado não prova ausência de conhecimento comum: a aproximação lexical e seus cortes são limitados e não foram calibrados semanticamente.

A cadeia com PDFs sintéticos foi executada até a incorporação e a compilação, incluindo repetição sem duplicatas, acréscimos ao acervo e falha de compilação sem perda das questões incorporadas. O adaptador do GitHub também foi executado localmente com suas variáveis de entrada e gerou a subpasta compilador no artefato previsto. Não foi iniciado um runner remoto do GitHub nesta verificação.

Arquivos reais/resultados gerados permaneceram em trabalho/, ignorados pelo Git. Exemplos versionados continuam fictícios e a base principal permanece vazia. Pesos e cortes iniciais são configuráveis; validar com uma amostra de pares declarados antes de usar os grupos como instrumento de análise do conteúdo exigido.
