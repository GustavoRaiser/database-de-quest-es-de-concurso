# Plano de desenvolvimento local

## Estado inicial

Formato 3, exemplos e CLI em Python implementados. Já existem leitura, validação, consulta com metadados, armazenamento de recursos por hash, registro de metadados e registro de lotes de questões existentes. A base principal continua vazia.

Ainda não há extrator de PDF, adaptador da Quest API, conversor/sanitizador de HTML, cadastro de categorias, inclusão de questões ou atualização de situação por comando. O registro de lote não faz essas importações.

## Etapa 1 — Preparar ambiente e fixar o contrato

- Clonar o repositório.
- Verificar a distinção entre nomes maiúsculos e minúsculos no volume local.
- Ler ESPECIFICACAO.md e usar exemplos/base como amostra independente.
- Escolher a linguagem e a interface inicial. A CLI atual usa Python 3.10 ou superior, sem dependências externas.
- Manter a versão 3 e as posições dos campos alinhadas ao manifesto.

Resultado: ambiente capaz de ler os arquivos de exemplo sem mudar sua estrutura.

## Etapa 2 — Leitor e validador

Implementar leitura do manifesto, catálogo, índice e JSONL. Diagnósticos devem apontar arquivo, linha e motivo, sem modificar os dados.

Verificações de aceitação:
- Questão 1 retorna a primeira linha e questão 10 retorna a décima.
- Zero, números negativos e linhas inexistentes não retornam outra questão.
- Situações 0, 1 e 2 funcionam; booleanos e outros valores são recusados.
- Listas com 0, 2, 5 e 100 assertivas são aceitas.
- Acentos, aspas, delimitadores ;; e quebras escapadas são preservados.
- Linhas vazias e registros quebrados em várias linhas são detectados.
- Catálogos sem pai, caminhos divergentes e índices inconsistentes são relatados.

Resultado: leitura confiável antes de desenvolver escrita.

## Etapa 3 — Cadastro da hierarquia

Implementar cadastro de órgão, cargo, disciplina e tema. Gerar códigos em base 62 por pai, sem reutilização. Serializar operações de cadastro para evitar códigos duplicados.

Ao criar tema, criar seu arquivo vazio e atualizar catálogo e índice com estratégia de recuperação caso uma etapa falhe. A ordem alfabética dos nomes não determina os códigos.

Resultado: hierarquia navegável, arquivos de temas existentes e índice consistente.

## Etapa 4 — Inclusão e importação

Validar todo o lote antes da escrita. Bloquear gravações concorrentes no arquivo, conferir sua integridade e anexar os registros. Retornar os IDs derivados das linhas resultantes.

Medir e definir a recuperação de uma gravação interrompida: não remover silenciosamente uma última linha danificada nem expor seu conteúdo como questão válida.

Resultado: novos registros entram ao final, preservando integralmente as linhas anteriores.

## Etapa 5 — Consulta e situação

Implementar busca por ID, listagem de tema, filtro por situação e atualização de situação.

Verificação principal: depois de atualizar uma situação, todos os IDs continuam apontando para os mesmos enunciados e assertivas. Depois de acrescentar questões, os IDs anteriores continuam iguais. Uma atualização concorrente não pode eliminar uma inclusão.

Resultado: consulta local e manutenção das situações 0/1/2.

## Etapa 6 — Índice e recuperação

Implementar conferência e reconstrução do índice a partir dos arquivos, comparando com os catálogos. Apresentar inconsistências antes de substituir o índice. Não remover questões para “consertar” a base.

Resultado: índice reconstruível sem depender de uma lista central de questões.

## Etapa 7 — Amostra real e desempenho

Importar uma pequena amostra autorizada e medir:
- Tamanho total, número de arquivos e maior tema.
- Tempo para ler primeira, intermediária e última questão.
- Tempo para validar a base e atualizar uma situação.
- Comportamento de backup e restauração.

Somente depois decidir se vale acrescentar índice de bytes, divisão de temas, compressão ou interface gráfica.

## Comandos previstos

Operações planejadas; consultar README.md para os comandos já disponíveis:

| Operação | Entrada | Saída |
|---|---|---|
| validar | Pasta da base | Diagnósticos |
| cadastrar | Tipo, pai e nome | Código e caminho |
| adicionar | Tema e registros | IDs cadastrados |
| consultar | ID completo | Situação e conteúdo |
| listar | Tema e filtro opcional | Questões com IDs |
| situacao | ID e novo código | Confirmação |
| reconstruir-indice | Pasta da base | Diferenças e índice validado |

## Fora do escopo inicial

Comentários, histórico de situações, movimentação de questões, correção textual, sincronização entre várias bases, deduplicação semântica, extração de PDF, conversão de HTML e integração remota. Gabaritos, procedência e imagens locais já possuem estrutura e validação em METADADOS.md.

## Cuidados operacionais

Não ordenar nem formatar automaticamente arquivos JSONL. Não resolver conflitos Git concatenando ou reordenando linhas: a posição faz parte do ID. Evitar que dois computadores acrescentem questões ao mesmo tema em paralelo sem coordenação. Mudanças no catálogo e nos arquivos devem ser revisadas antes de integrar versões.

## Entrega mínima utilizável

Leitor, validador, cadastro, inclusão, consulta, atualização de situação e reconstrução do índice, com verificações de preservação de linhas e gravação segura. Não é necessário construir uma interface web para começar.

Implementada a preparação de abordagem via tarefa para IA/harness e o registro validado de perfis com evidências, hash, autoria e histórico. Os comandos preparar-abordagem e registrar-abordagens são executáveis. O modelo é executado pelo harness; scores e agrupamentos permanecem futuros.
