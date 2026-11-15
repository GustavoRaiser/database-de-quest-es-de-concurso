# Arquitetura por agentes

Cada pasta de trabalho equivale a um funcionário especializado. O repositório reúne seus resultados, sem fundir as ferramentas e instruções de funções diferentes.

## Organizador

Missão: definir e manter a organização da base e permitir que ferramentas encontrem e interpretem os registros.

Possui o contrato do armazenamento definitivo: hierarquia, IDs, JSONL, metadados _md.json, arquivos de recursos e registros de lotes. Seu código, documentação, testes e exemplos ficam em organizador/.

Já implementa consulta, validação, armazenamento de recursos, registro de metadados e registro de lotes referentes a questões existentes. Reserva de órgão/cargo e inclusão de novas questões via incorporar-extracao estão implementadas, com publicação recuperável. Atualização de situação por comando genérico permanece planejada. Portanto, ele é um sistema de organização de dados com ferramentas auxiliares; não é um digitalizador nem uma plataforma de resolução de questões.

A base principal vazia tem seu manifesto na raiz do módulo organizador/. A amostra em organizador/exemplos/base/ é outra base, independente. Caminhos dentro dos manifestos são relativos à base correspondente.

## Digitalizador

Missão: transformar a fonte em conteúdo estruturado fiel, identificando perdas e dúvidas.

Terá código próprio para PDF, imagem/OCR, layout, HTML e adaptação de entradas estruturadas, com testes e dependências na própria pasta digitalizador/. Preserva número original, página, versão de caderno, fontes e materiais de apoio. Não inventa informações ausentes nem avalia automaticamente a atualidade jurídica.

Entrega candidatos e relatórios; não escreve no acervo definitivo. O extrator ENAM/FGV Tipo 1 já foi implementado; ver digitalizador/README.md.

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
                  ├→ Emissor: consulta da base com metadados e recursos
                  └→ Compilador: relações e grupos → CLI/ferramentas próprias
```

A extração do perfil ENAM/FGV Tipo 1 já está ligada à captação e à interface. O pipeline já chama o Organizador para incorporação definitiva de extrações v2 sem bloqueios técnicos; temas incertos ficam Não classificado. Não há etapa obrigatória de revisão jurídica nem agente de atualização automática. A desatualização é informada manualmente pelo usuário.

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

Captador implementado em captador/: entrada por upload ou seleção manual de pasta, lotes por prova/edição/caderno e associação de gabaritos/retificações à prova. A área Adicionar material no Emissor consome sua CLI pública. A prévia é documental, com hashes e pendências. O Digitalizador extrai o perfil ENAM/FGV Tipo 1 em formato intermediário; a incorporação pelo Organizador já está implementada. O gabarito pode chegar depois. A situação jurídica da questão é informada pelo usuário.

O Captador usa protocolos órgão.cargo.prova e mantém registro filtrável e histórico. A barreira de encaminhamento exige prova e gabarito íntegros e vinculados, além da identificação. A fila registra um pacote, não a execução. Análise concluída/falha pode ser declarada manualmente pelo usuário com relatório.

A preparação temática do Organizador agora fornece uma tarefa de abordagem à IA/harness e registra o perfil fundamentado nos metadados. O Compilador usa esses perfis e o texto exportado para buscar candidatas e calcular indícios lexicais de semelhança. Comparação, score e grupos propostos estão implementados; equivalência semântica não é confirmada.

## Operação por código no host

A cadeia de URL/arquivos até extração e descritores locais funciona sem IA para o perfil suportado. O Emissor apresenta a prévia; o acervo definitivo é preservado. Descritores lexicais não são equiparados a interpretação semântica. Interfaces históricas para harness não são chamadas nesse fluxo.

O workflow GitHub Actions e o desktop executam as mesmas CLIs. Captador reserva fontes no ambiente receptor; Digitalizador coordena o percurso e Organizador publica a base. Artefatos não são sincronizados entre ambientes sem uma transferência explícita. Ver [operação](digitalizador/OPERACAO.md).

## Compilador

Pasta compilador/: recebe um snapshot público do Organizador, busca candidatas por índice invertido, compara os quatro critérios, registra scores e propõe grupos com vínculo direto entre todos os membros. Pode executar sozinho ou após a incorporação no pipeline. Salva resultados derivados e índices de vizinhos em sua própria pasta de trabalho, sem modificar dados/metadados/IDs. O Emissor continua consultando o acervo e ainda não mostra grupos na tela. Ver compilador/README.md.

Fluxo atual: Captador → Digitalizador → Organizador → Compilador; o Emissor consulta o acervo em paralelo e poderá consumir as relações pela CLI. No GitHub, o artefato inclui as compilações do mesmo ambiente; no desktop, elas ficam locais.

## Modo semântico adicional

Implementado o modo conjunto lexical + IA local no Compilador, com saídas separadas, registro de execução, identificação de modelos, evidências e cache. A autorização de IA limita-se ao Compilador; os demais módulos seguem por código convencional. Ver [compilador/SEMANTICA.md](compilador/SEMANTICA.md). O serviço Ollama e modelos precisam estar instalados no ambiente executor; a avaliação real dos modelos e a preparação de runner semântico permanecem pendentes.
