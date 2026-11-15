# Revisão geral de funcionalidades e integração — 15/11/2026

A cadeia executável está completa para o perfil ENAM/FGV Tipo 1 textual: Captador → Digitalizador → Organizador → Compilador. A interface Emissor consulta o acervo e permite captação/extração, mas termina na prévia intermediária. A operação de ponta a ponta exige a CLI do pipeline ou o workflow manual de processamento. O projeto ainda não é um importador universal de concursos nem uma análise semântica de cobrança.

## Correções desta revisão

| Prioridade | Problema confirmado | Correção/verificação |
|---|---|---|
| Alta | Falha ao ler um pedido ou preparar a execução podia conservar o relatório anterior com completo=true | Relatórios passam por estado inicial e publicação atômica; erros geram falha explícita. Testes com relatório antigo de sucesso e pedido inválido |
| Alta | Reserva corrompida no início de uma listagem interrompia a captação dos pares seguintes; URLs repetidas também repetiam processamento no mesmo pedido | Isolamento do erro por reserva e deduplicação da lista de reservas retornada; testes de corrupção seguida por par válido e repetição de página |
| Média | Compilador alinhava a lista concatenada de campos; com números diferentes de alternativas, podia comparar apoio com alternativa e inflar a semelhança | Comparação por tipo e posição: enunciado, assertiva e apoio. Algoritmo lexical/2; resultados antigos continuam arquivados. Teste específico de campos deslocados |
| Média | Cópia inicial da base no runner ficava visível antes de completar, permitindo que uma retomada usasse cópia incompleta | Preparação em diretório temporário e publicação por renomeação ao final; base existente continua sujeita à validação do Organizador |
| Média | Não havia verificação automática dos módulos em alterações no GitHub | Workflow de testes em push/main, pull request e execução manual, com Linux/Windows e validação das bases |
| Baixa | Planos/documentos diziam que funcionalidades já implementadas ainda eram futuras | Documentação do Captador/Emissor alinhada ao código; distinguida a prévia visual da cadeia CLI completa |

## Mapa funcional verificado

| Passagem | Como funciona | Limite atual |
|---|---|---|
| URLs/pasta → Captador | HTTPS público com limite de tamanho/redirecionamentos; cartões Qconcursos; pares _cad/_gab; cópia e hash dos originais | Não acompanha pasta continuamente nem percorre páginas seguintes automaticamente. Metadados não reconhecidos exigem informação adicional |
| Captador → Digitalizador | Protocolo, identificação, prova e gabarito; pacote atual, hashes e vínculo obrigatórios | Nome do par é declaração de associação. Perfil/caderno conferido pelo extrator; não garante associação semântica de qualquer PDF |
| Digitalizador → Organizador | Contrato intermediário v2, numeração, alternativas, respostas, recursos e bloqueios; chamada à CLI pública | Só ENAM/FGV Tipo 1 textual. Sem OCR; complemento/retificação não interpretado bloqueia incorporação |
| Organizador → acervo | Reserva de IDs, inclusão ao final, metadados por linha, fontes por hash, ficha de prova, transação recuperável | Mesmo PDF no mesmo órgão/cargo é idempotente; outro gabarito não atualiza automaticamente questões já incorporadas |
| Organizador → Compilador | Snapshot validado sob bloqueio, com questões/perfis/ocorrências e hash | Exportação carrega o recorte inteiro em memória. Grandes acervos precisam de medição e exportação incremental futura |
| Compilador → resultados | Índice de candidatas, scores/cobertura/evidências, grupos conservadores e resultados por hash | Scores lexicais; busca limitada pode perder relações. Não deduplica aplicações/cadernos nem calcula frequência/recência |
| Acervo → Emissor | CLI pública, filtros combináveis, paginação, metadados e recursos; servidor localhost | Grupos não aparecem na interface. Prévia da extração não oferece incorporação/compilação visual |
| Desktop ↔ GitHub | Mesmas CLIs; runner produz artefato com originais/base/compilações; pode restaurar artefato anterior | Sem sincronização implícita ou merge de acervos. Artefatos expiram em 30 dias |

## Automação real e pontos que exigem ação

O processamento começa por um comando, uma ação na interface ou Run workflow. Depois que um pedido válido entra pelo pipeline, os lotes suportados percorrem as etapas automaticamente e a compilação ocorre uma vez ao final. Não há agendamento periódico, serviço residente nem monitoramento de pasta implementados. Publicar arquivos no GitHub não inicia o workflow de processamento; o novo workflow automático executa testes, não capta provas.

O Captador reserva conteúdo desconhecido/incompleto e relata pendências; não inventa identificação ou condição definitiva de gabarito. O hash conhecido do gabarito ENAM 2026.1 permite reconhecer sua condição; outros exigem declaração. Um pedido com várias edições não deve receber uma identificação global que force todas para a mesma edição.

Reexecução da mesma prova conserva IDs. A extração ainda é refeita antes de o Organizador detectar a incorporação existente: há idempotência de dados, mas não cache completo de execução por etapa. Recomenda-se adicionar checkpoint/cache de extração com hashes de entrada/implementação antes de escalar a coleta.

Interrupções de publicação do Organizador podem ser retomadas por recuperar. Bloqueios deixados por processo encerrado exigem conferência antes de remoção; não são apagados automaticamente. Corrupção de lotes existentes pode bloquear preparação de novos encaminhamentos para evitar conflitos de protocolo. A correção desta revisão isola falhas de **recepção**, sem relaxar essa verificação de integridade.

## Validação executada

100 testes locais aprovados: Captador 25, Digitalizador/pipeline 9, Organizador 38, Compilador 17 e Emissor 11. Incluem ciclo com PDFs sintéticos, incorporação, repetição sem duplicatas, acréscimos preservando linhas, anulação, recusa de gabarito substituído, recuperação transacional, falha do Compilador sem perda de questões, proteção HTTP, recursos, filtros e novas regressões.

Bases principal vazia e fictícia validadas. Também reexecutado o pipeline com o par real ENAM 2026.1 já reservado localmente, sem novo download: retomou o lote, reaproveitou os IDs e executou a compilação. PDFs e resultados reais permaneceram nas pastas ignoradas pelo Git.

O YAML dos workflows foi conferido. As verificações locais ocorreram em Linux; a matriz Windows/Linux no GitHub deve ser acompanhada em Actions. Publicação de um workflow não equivale a execução remota aprovada. Esta revisão não fez auditoria externa de segurança, avaliação jurídica do conteúdo nem medição de precisão semântica. Não houve nova coleta ao vivo do site Qconcursos; a descoberta foi coberta pelos testes e pelos artefatos da execução real anterior.

## Próximas prioridades

1. Conectar a interface à conclusão do pipeline e à consulta dos grupos, com estados por etapa e acesso aos recursos originais na prévia. Hoje essa conclusão é pela CLI/workflow.
2. Implementar retomada por reserva/lote sem redescobrir páginas e cache por etapa, com relatório durável por execução. Evitar sobrescrever relatórios históricos quando for necessário auditar várias execuções.
3. Ampliar extratores usando amostras de outros layouts e OCR; testar tabelas, figuras, fórmulas e textos de apoio compartilhados. Preservar o PDF é necessário, mas não demonstra equivalência visual da versão em texto.
4. Criar fluxo explícito de retificação de gabarito/situação e de classificação temática confirmada, preservando IDs e histórico.
5. Calibrar scores com pares rotulados; medir recuperação da busca aproximada contra uma amostra exaustiva. Só depois tratar grupos como insumo de estatísticas de cobrança.
6. Definir backup e política de continuidade entre ambientes; medir custo de validação, leitura por linha, cópia de estágio e exportação em acervos maiores. A versão atual prioriza integridade e não foi validada para milhões de questões.

Essas prioridades são recomendações de revisão, não funcionalidades já implementadas. O formato principal, os IDs por linha e os originais permanecem preservados.
