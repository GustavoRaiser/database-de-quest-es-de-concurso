# Arquitetura por agentes

Cada pasta de trabalho equivale a um funcionário especializado. O repositório reúne seus resultados, sem fundir as ferramentas e instruções de funções diferentes.

## Organizador

Missão: definir e manter a organização da base e permitir que ferramentas encontrem e interpretem os registros.

Possui o contrato do armazenamento definitivo: hierarquia, IDs, JSONL, metadados _md.json, arquivos de recursos e registros de lotes. Seu código, documentação, testes e exemplos ficam em organizador/.

Já implementa consulta, validação, armazenamento de recursos, registro de metadados e registro de lotes referentes a questões existentes. Cadastro de categorias, inclusão de novas questões e atualização de situação via comando ainda estão planejados. Portanto, ele é um sistema de organização de dados com ferramentas auxiliares; não é um digitalizador nem uma plataforma de resolução de questões.

A base principal vazia tem seu manifesto na raiz do módulo organizador/. A amostra em organizador/exemplos/base/ é outra base, independente. Caminhos dentro dos manifestos são relativos à base correspondente.

## Digitalizador

Missão: transformar a fonte em conteúdo estruturado fiel, identificando perdas e dúvidas.

Terá código próprio para PDF, imagem/OCR, layout, HTML e adaptação de entradas estruturadas, com testes e dependências na própria pasta digitalizador/. Preserva número original, página, versão de caderno, fontes e materiais de apoio. Não inventa informações ausentes nem avalia automaticamente a atualidade jurídica.

Entrega candidatos e relatórios; não escreve no acervo definitivo. Sua estrutura documental está preparada, mas nenhum extrator foi implementado nesta reorganização.

## Fluxo de trabalho previsto

```text
Fonte (PDF / imagem / conteúdo estruturado)
                  ↓
Captador: recepção, originais e associação de documentos
                  ↓
Digitalizador: extração + procedência + pendências
                  ↓
Entrega intermediária, ainda sem ID local definitivo
                  ↓
Preparação técnica e classificação; situação informada pelo usuário
                  ↓
Organizador: validação + armazenamento + ID local por linha
                  ↓
Emissor: consulta e visualização conjunta de questão, metadados e recursos
```

As etapas futuras de extração e inclusão não estão ligadas por automação hoje. O contrato de entrega deve ser implementado antes dessa conexão. Não há etapa obrigatória de revisão jurídica nem agente de atualização automática. A desatualização é informada manualmente pelo usuário.

## Organização física de um tema

```text
BASE/dados/ORGAO/CARGO/DISCIPLINA/
    TEMA.jsonl
    TEMA_md.json
```

Não há pasta TEMA na versão 3. Não há ID explícito em cada linha de questões. O arquivo de metadados é um objeto esparso indexado pela linha decimal: {"3": {...}, "80": {...}}. As posições de suas próprias linhas não têm significado.

## Regra de propriedade

Uma função deve ter um responsável principal. Extração pertence ao Digitalizador; organização definitiva pertence ao Organizador. Interfaces e contratos podem ser compartilhados, mas implementações e instruções específicas permanecem nas respectivas pastas. A raiz registra decisões globais, sem se tornar uma terceira ferramenta genérica.

## Emissor

Pasta emissor/: interface no navegador e API JSON de leitura, com filtros opcionais de órgão, cargo, disciplina e tema. Sem filtros, toda a base participa da consulta paginada. Inclui metadados, textos de apoio e recursos; mostra a situação como cadastrada. Usa a CLI pública do Organizador, sem importar seu código interno. Já implementado para execução local, sem hospedagem automática pelo GitHub.

## Captador e interface compartilhada

Captador implementado em captador/: entrada por upload ou seleção manual de pasta, lotes por prova/edição/caderno e associação de gabaritos/retificações à prova. A área Adicionar material no Emissor consome sua CLI pública. A prévia é documental, com hashes e pendências. O Digitalizador segue planejado; nenhuma questão é extraída ou incorporada automaticamente ao Organizador. O gabarito pode chegar depois. A situação jurídica da questão é informada pelo usuário.

O Captador usa protocolos órgão.cargo.prova e mantém registro filtrável e histórico. A barreira de encaminhamento exige prova e gabarito íntegros e vinculados, além da identificação. A fila registra um pacote, não a execução. Análise concluída/falha pode ser declarada manualmente pelo usuário com relatório.
