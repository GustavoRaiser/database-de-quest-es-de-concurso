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
