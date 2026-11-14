# Planejamento do Digitalizador

## Estado

Somente estrutura e instruções. Não há ferramenta de processamento implementada. Esta reorganização prepara o trabalho futuro sem misturar funções com o Organizador.

## Etapas

1. Escolher uma prova e seu gabarito oficial do mesmo caderno; primeiro alvo previsto: ENAM/FGV.
2. Definir e versionar o contrato intermediário de candidatos, procedência, recursos e pendências, com exemplos validáveis.
3. Definir a estrutura de código, testes, dependências, entradas e saídas dentro de digitalizador/.
4. Implementar primeiro a extração de PDF com texto e tratamento de colunas, cabeçalhos e continuidade entre páginas.
5. Conferir numeração, alternativas e gabarito. Separar estado de anulação de avaliação de atualidade jurídica.
6. Produzir prévia e relatório de elementos não representados; preservar o documento original e seus hashes.
7. Implementar testes com exemplos de layout e comparar o resultado com a fonte.
8. Definir a entrega revisada ao Organizador sem escrever diretamente no acervo. A inclusão de novas questões ainda precisa ser implementada no Organizador.
9. Avaliar execução por GitHub Actions e, depois, OCR e adaptadores de HTML/JSON, conforme a necessidade.

## Critério de primeira entrega

Extrair um caderno escolhido, manter enunciados e alternativas na ordem correta, identificar recursos necessários e informar pendências sem omissões silenciosas. A execução deve poder ser reproduzida com a mesma fonte e versão do extrator. A automação de incorporação à base definitiva é uma etapa posterior.
