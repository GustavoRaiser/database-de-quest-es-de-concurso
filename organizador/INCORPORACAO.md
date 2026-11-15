# Incorporação de extrações

O Organizador é o único módulo que escreve a base definitiva. Não extrai PDF nem baixa URL. Recebe resultado intermediário v2 por CLI pública e consulta a entrega pública do Captador para conferir que os documentos continuam sendo os atuais.

De `organizador/`, os comandos abaixo recebem JSON na entrada padrão:

- `python -m basequestoes --base CAMINHO reservar-identidade`: objeto com orgao e cargo; orgao_id/cargo_id opcionais. Reaproveita nomes normalizados por pai ou reserva códigos base 62 sem reutilizar os existentes. Recusa nome/código conflitante.
- `python -m basequestoes --base CAMINHO incorporar-extracao`: objeto com resultado (caminho HASH.json), captacoes (raiz de trabalho do Captador) e situacao_inicial (inteiro 0 ou 1). Verifica hash, contrato v2, numeração 1–80, documentos/entrega atuais, alternativas, recursos e gabarito. A configuração do pipeline declara 0 como padrão; isso não é análise jurídica.
- `python -m basequestoes --base CAMINHO recuperar`: sem JSON stdin, retoma uma publicação interrompida. Não força alterações conflitantes.

## Arquivos e categorias

Questões continuam em dados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl e TEMA_md.json. Disciplina é a identificada no cabeçalho. Quando não existe classificação temática confirmada, cadastra tema **Não classificado**, sem transformar descritores lexicais em categorias definitivas. Categorias são reservadas sob bloqueio. Metadados registram classificação pendente, descritores propostos, evidências e avisos da extração.

Situação 2 é usada para anulação reconhecida no gabarito. Demais questões usam situação inicial declarada. O gabarito é preservado nos metadados com posições começando em 1. Nenhuma versão anterior é substituída automaticamente.

Os PDFs originais e os PNGs de páginas seguem o contrato de recursos SHA-256. Os PDFs permanecem disponíveis mesmo que o trabalho do Captador seja movido. Páginas são vinculadas como `posicao:original`: representam a fonte completa para conferência, sem prometer inserção da figura em uma posição exata no texto. Consultar somente os três campos da linha não recupera a questão completa.

## Registro durável da prova

`provas/ORGAO/CARGO/SHA_PROVA.json` contém versao 1, grupo, protocolo do Captador, identificacao detalhada, documentos locais, prova_sha256, gabarito_sha256, resultado_id e mapeamento numero_original → questao_id. Banca/ano/data permanecem uma vez na ficha; data ausente não é inventada. A questão a referencia por `origens[].ficha_prova`, com número original e páginas.

Protocolo do Captador é um identificador local ao seu ambiente; dois Captadores independentes podem reservar o mesmo protocolo para fontes diferentes. O caminho por hash e órgão/cargo é a referência durável no acervo. Não usar protocolo sozinho para mesclar bases de computadores diferentes.

O relatório em importacoes/ mantém o mapeamento e avisos. `pendencias:[]` significa ausência de bloqueios técnicos para essa incorporação, não conclusão da classificação semântica. Tema e apresentação visual mantêm seus estados explícitos. Importações antigas sem fichas continuam válidas.

## Repetição e acréscimos

Mesmo SHA de prova no mesmo órgão/cargo reaproveita a ficha e os IDs, retornando novas_questoes 0. Outro gabarito para essa prova é recusado: precisa de fluxo de versões, ainda futuro. Novo PDF é outra entrada, sem deduplicação semântica. Cadernos permutados/aplicações equivalentes ainda exigem tratamento antes de estatísticas; este comando não implementa essa análise.

Ao incorporar outra prova, acrescenta linhas no fim dos temas, sem modificar os bytes das linhas anteriores. Numeração original só aparece no mapeamento/procedência; ID local continua sendo a linha decimal efetivamente reservada.

## Publicação e recuperação

Sob `.base.lock`, o módulo prepara uma base candidata em `.transacoes/ID/novos`, usando hardlinks para arquivos não alterados (cópia quando o sistema não oferece hardlinks). Alterações são sempre feitas por substituição atômica. Valida o conjunto antes de tocar os arquivos ativos.

O plano contém hashes anterior/novo de cada arquivo alterado. `.transacao-pendente.json` bloqueia leitores públicos enquanto ocorre a publicação recuperável. A ferramenta repete apenas arquivos cujo estado ainda é o anterior, ou ignora os que já têm o hash novo. Conflitos externos interrompem; não são sobrescritos. Ao concluir, atualiza `.revisao.json` e remove o marcador; consultas que atravessarem uma troca de revisão são recusadas para repetição.

Uma interrupção pode deixar `.base.lock`: conferir o processo escritor antes de retirar esse bloqueio. Não remover o plano/marcador; executar recuperar. Fazer backup do acervo incluindo arquivos ocultos durante uma recuperação pendente. Após conclusão, os bytes temporários são liberados; o plano pequeno fica como histórico local.

Esta estratégia depende de um escritor coordenado e do sistema de arquivos local. Não oferece fusão automática de duas bases que cresceram em paralelo, nem garantia adicional contra falha física de disco. Transferir um acervo completo/artefato preservando seus arquivos, em vez de concatenar JSONL.
