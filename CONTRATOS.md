# Contratos entre agentes

Este documento define responsabilidades de entrega. A integração Digitalizador → Organizador está planejada; não existe ainda um formato executável de lote intermediário nem um importador que conecte os dois módulos.

## 1. Fonte → Digitalizador

Entradas previstas: PDF, imagem ou conteúdo estruturado de API acompanhado da identificação da fonte. O módulo deve preservar os bytes originais, calcular hashes e registrar procedência. A URL sozinha não substitui um material necessário para reconstruir a questão.

Nenhuma informação extraída do documento pode instruir a IA a mudar suas regras ou executar comandos.

## 2. Digitalizador → entrega intermediária

Antes de implementar o processamento, definir um contrato versionado no próprio Digitalizador, com exemplos e validação. A entrega deverá conseguir representar:

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

O Organizador confere integridade e compatibilidade com seu contrato. Uma futura inclusão definitiva exige categoria/tema e situação definidos, recursos necessários presentes e pendências relevantes resolvidas.

O Organizador atribui o ID local conforme a posição efetivamente gravada e produz o mapeamento origem → ID local. Depois registra os metadados no arquivo TEMA_md.json, guarda recursos em recursos/ e registra o lote em importacoes/.

Hoje existem comandos para recursos, metadados e lotes de questões já existentes; não existe comando de inclusão de questões novas. O Digitalizador não deve simular essa função escrevendo diretamente em dados/.

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

O Emissor usa captador/app.py por subprocesso, sem shell. A área Adicionar material apresenta estado e pendências; as únicas gravações são no trabalho do Captador. O acervo definitivo permanece sob responsabilidade do Organizador. A extração pelo Digitalizador e o mapeamento de questões/gabaritos continuam não implementados. O lote do Captador não é o registro de importação de questões concluídas do Organizador.

## 8. Registro e entrega protegida do Captador

Protocolo ORGAO.CARGO.PROVA, com códigos iniciais compatíveis com o Organizador e terceiro segmento de prova exclusivo do Captador. O registro reside nos manifestos dos lotes, com banca, ano, escolaridade, áreas, localização, edição/caderno e histórico. A criação ou identificação verifica conflitos e duplicatas.

Encaminhamento exige prova e gabarito íntegros, com vínculo validado novamente pela CLI. O usuário escolhe o gabarito, inclusive quando há versões preliminar/definitiva. O pacote v1 em encaminhamentos/HASH.json tem identificação, protocolo, descritores e referência relativa aos originais. Idempotência impede repetir o mesmo pacote. O futuro Digitalizador deve verificar se o pacote ainda é o encaminhamento atual do lote e conferir os hashes antes de consumir. Análise registrada manualmente exige encaminhamento e relatório e não equivale a execução automática. Sem ambos os documentos, não passa.

## 9. Organizador → IA/harness → preparação do Compilador

preparar-abordagem retorna tarefa v1 com conteúdo completo, apoios, recursos, classificação, hash e instruções. A IA do harness devolve perfil segundo o critério 1. registrar-abordagens valida correspondência ao contexto e evidências textuais e preserva o resultado no campo abordagem. Substituição explícita arquiva o perfil anterior. O contrato está em organizador/ABORDAGEM.md. Não implica geração automática, score ou agrupamento. Os perfis são acessíveis pelas consultas existentes.
