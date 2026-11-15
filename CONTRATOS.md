# Contratos entre agentes

Este documento define responsabilidades de entrega. Existe formato intermediário de extração em digitalizador/CONTRATO.md. A incorporação definitiva é executada pelo Organizador a partir da extração v2.

## 1. Fonte → Digitalizador

Entradas previstas: PDF, imagem ou conteúdo estruturado de API acompanhado da identificação da fonte. O módulo deve preservar os bytes originais, calcular hashes e registrar procedência. A URL sozinha não substitui um material necessário para reconstruir a questão.

Nenhuma informação extraída do documento pode instruir a IA a mudar suas regras ou executar comandos.

## 2. Digitalizador → entrega intermediária

O perfil ENAM/FGV Tipo 1 já tem contrato versionado no Digitalizador, exemplos e validação. A evolução da entrega deve preservar:

- Fonte, data de coleta, hashes, versão do extrator e identificação do lote.
- Identificação da questão na origem, número original, páginas e caderno, quando disponíveis.
- Enunciado e alternativas na ordem original, conservando seus rótulos.
- Textos de apoio e recursos, com a posição de apresentação e referências locais.
- Representação original de HTML/JSON quando necessária para conferir a conversão.
- Gabarito e sua condição (ausente, preliminar, definitivo ou anulado), quando documentados pela fonte.
- Classificações propostas e dúvidas, sem apresentá-las como decisões definitivas.
- Pendências de extração, elementos não representados e limitações conhecidas.

O candidato usa identidade de origem ou temporária, não o ID definitivo por linha do Organizador. Não fixar questão 1 local apenas porque seu número original é 1.

Artefatos de trabalho e saídas de extração pertencerão ao Digitalizador. O módulo deverá documentar seus caminhos e política de armazenamento antes de gerar acervos grandes. Não colocar saídas ainda não revisadas no diretório de questões do Organizador.

## 3. Entrega revisada → Organizador

O Organizador confere integridade e compatibilidade com seu contrato. A incorporação exige situação inicial declarada, categoria/tema (admite Não classificado), recursos preservados e nenhum bloqueio técnico. Avisos lexicais e de apresentação visual permanecem nos metadados/relatório.

O Organizador atribui o ID local conforme a posição efetivamente gravada e produz o mapeamento origem → ID local. Depois registra os metadados no arquivo TEMA_md.json, guarda recursos em recursos/ e registra o lote em importacoes/.

O comando incorporar-extracao inclui novas questões, metadados, fontes e fichas da prova. reservar-identidade cadastra órgão/cargo. Ambos usam publicação transacional validada e recuperável. O Digitalizador não deve simular essa função escrevendo diretamente em dados/.

## 4. Consulta

Quem consumir uma questão completa deve usar o leitor do Organizador ou reproduzir seu contrato: linha de TEMA.jsonl + chave correspondente em TEMA_md.json + recursos referenciados. Ler apenas o JSONL pode deixar de fora conteúdo necessário.

## 5. Mudanças

Alterar o armazenamento exige atualizar especificações, manifesto e testes do Organizador conforme o impacto. Alterar a entrega de extração exige versionar o contrato intermediário do Digitalizador. Uma alteração não deve mudar silenciosamente o formato do outro módulo.

## 6. Organizador → Emissor → ferramentas do usuário

A CLI pública do Organizador oferece catalogos e emitir. emitir aceita --orgao, --cargo, --disciplina e --tema com as chaves completas dos respectivos catálogos, além de --pagina e --por-pagina. Filtros vazios são omitidos e os preenchidos se combinam por interseção. Nenhum filtro significa toda a base, com paginação. A resposta JSON traz itens, total, pagina, por_pagina e paginas. Cada item reúne id, questao, metadados e classificacao.

O Emissor consome essa interface por subprocesso sem shell e publica /api/catalogos e /api/questoes, documentados em emissor/README.md. Recursos seguem o contrato local de SHA-256. Operações são de leitura; não acrescentam questões nem alteram situações. Ferramentas próprias podem consumir a CLI, a API local ou o formato documentado diretamente.

A desatualização é declarada pelo usuário. Não existe revisão jurídica obrigatória nem monitoramento automático de atualidade neste fluxo.

## 7. Captador → Digitalizador e interface compartilhada

Contrato de captação versão 2 documentado em captador/README.md. Entrada: arquivo enviado ou selecionado em entrada/. Saída: recebidos/ID/lote.json e originais preservados por hash, um lote por prova/caderno. Gabarito e retificação apontam ao hash da prova. A correspondência de caderno é declarada pelo usuário.

O Emissor usa captador/app.py por subprocesso, sem shell. A área Adicionar material apresenta estado e pendências; as gravações de recepção são no trabalho do Captador, e resultados intermediários pertencem ao trabalho do Digitalizador. O acervo definitivo permanece sob responsabilidade do Organizador. O Digitalizador extrai o perfil suportado e associa o gabarito pelo número original; o Organizador produz o mapeamento para IDs definitivos na incorporação. O lote do Captador não é o registro de importação de questões concluídas do Organizador.

## 8. Registro e entrega protegida do Captador

Protocolo ORGAO.CARGO.PROVA, com códigos iniciais compatíveis com o Organizador e terceiro segmento de prova exclusivo do Captador. O registro reside nos manifestos dos lotes, com banca, ano, escolaridade, áreas, localização, edição/caderno e histórico. A criação ou identificação verifica conflitos e duplicatas.

Encaminhamento exige prova e gabarito íntegros, com vínculo validado novamente pela CLI. O usuário escolhe o gabarito, inclusive quando há versões preliminar/definitiva. O pacote v1 em encaminhamentos/HASH.json tem identificação, protocolo, descritores e referência relativa aos originais. Idempotência impede repetir o mesmo pacote. O Digitalizador verifica se o pacote ainda é o encaminhamento atual do lote e conferir os hashes antes de consumir. Análise registrada manualmente exige encaminhamento e relatório e não equivale a execução automática. Sem ambos os documentos, não passa.

## 9. Organizador → IA/harness → preparação do Compilador

preparar-abordagem retorna tarefa v1 com conteúdo completo, apoios, recursos, classificação, hash e instruções. A IA do harness devolve perfil segundo o critério 1. registrar-abordagens valida correspondência ao contexto e evidências textuais e preserva o resultado no campo abordagem. Substituição explícita arquiva o perfil anterior. O contrato está em organizador/ABORDAGEM.md. Não implica geração automática, score ou agrupamento. Os perfis são acessíveis pelas consultas existentes.

## 10. Operação atual sem IA

A implementação vigente é executada por programas no host. Descoberta/download no Captador, entrega completa e validada, extração ENAM/FGV Tipo 1 no Digitalizador e descritores por regras no Organizador. O contrato intermediário v2 está em digitalizador/CONTRATO.md. A interface consome as CLIs públicas e apresenta a extração via POST /api/digitalizacao/processar. O pipeline CLI chama a incorporação definitiva do Organizador e depois o Compilador, que propõe relações/grupos lexicais. Os modos históricos de tarefas para IA/harness não são dependências da operação atual.

## 11. Recepção em lote e operação portátil

`captador/app.py receber` recebe JSON com urls (páginas ou pares de URLs com sufixos/padrão Qconcursos), prova_url/gabarito_url explícitos, ou pasta com pares NOME_cad.pdf/NOME_gab.pdf. Todos os links dos cartões da página informada são reservados em reservados/ID/, com registro.json e cópias _cad/_gab; páginas seguintes exigem suas próprias URLs. Nome comum é declaração do vínculo, não inferência de resposta. Recepção conserva pares incompletos sem encaminhar.

`preparar-reserva` exige reserva completa, identificação e situação do gabarito; apenas hashes previamente conferidos dispensam declaração da situação. Reutiliza lotes compatíveis e chama encaminhar. O contrato do lote permanece v2 e o pacote de entrega v1. A convenção por arquivos não relaxa a conferência de caderno/numeração realizada pelo Digitalizador.

`digitalizador/pipeline.py` chama CLIs públicas de cada agente e produz relatório por reserva; segue processando outros itens quando um deles fica pendente. Só o Organizador escreve dados/. `incorporar-extracao` recebe resultado, captacoes e situacao_inicial por JSON stdin. Confere resultado v2 e entrega atual, preserva PDFs/recursos, cria ficha em provas/ORGAO/CARGO/SHA_PROVA.json e retorna mapeamento. Mesmo PDF no mesmo órgão/cargo é idempotente; gabarito diferente bloqueia atualização automática. A ficha é o vínculo durável; protocolo do Captador é local ao ambiente, não chave global entre computadores.

O workflow executa a mesma cadeia em runner do GitHub; preserva tudo em artefato, sem commit automático. Desktop guarda localmente. Continuar artefato anterior é explícito. Não há chamadas a modelos ou sincronização implícita entre os ambientes. Ver digitalizador/OPERACAO.md.

## 12. Organizador → Compilador → consumidores

A CLI pública exportar recebe os mesmos filtros de emitir e retorna um snapshot v1 completo de questões, metadados/classificação e fichas de prova, sem paginação. O Organizador valida o conjunto, verifica marcador/revisão de publicação e calcula corpus_sha256. Contrato da serialização canônica e resultados em compilador/CONTRATO.md. O Compilador chama a CLI por subprocesso, sem importar código interno.

O Compilador preserva IDs/ocorrências e escreve somente artefatos derivados. analisar gera scores por par e grupos propostos; comparar e similares oferecem consulta por ID; consultar lê resultado arquivado por hash. Nenhuma relação lexical altera o tema ou confirma equivalência semântica. Não identificado/indeterminado não é coincidência positiva. Grupos não aplicam transitividade.

O pipeline chama analisar uma vez após as incorporações bem-sucedidas do pedido, sobre todo o acervo, com saída definida por --compilacoes. Falha dessa etapa é registrada separadamente e não desfaz as incorporações já validadas; torna a execução incompleta. No GitHub, compilador/ acompanha o artefato acervo-processado. Emissor ainda não apresenta os grupos na interface visual.

## Modo semântico adicional

Implementado o modo conjunto lexical + IA local no Compilador, com saídas separadas, registro de execução, identificação de modelos, evidências e cache. A autorização de IA limita-se ao Compilador; os demais módulos seguem por código convencional. Ver [compilador/SEMANTICA.md](compilador/SEMANTICA.md). O serviço Ollama e modelos precisam estar instalados no ambiente executor; a avaliação real dos modelos e a preparação de runner semântico permanecem pendentes.
