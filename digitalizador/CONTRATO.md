# Extração intermediária v2 — enam_fgv/2

Entrada: encaminhamento atual validado pela CLI `entrega` do Captador. Exige prova e gabarito PDF, caderno Tipo 1, capa ENAM/edição correspondente, duas colunas, 80 questões A–E e layout de respostas reconhecido. Não é um extrator universal.

Saída: objeto `versao:2`, `extrator:enam_fgv/2`, encaminhamento, protocolo, identificacao, documentos, questoes, pendencias, bloqueios, estado, contagens, dependencias e implementacao_sha256. Cada questão tem numero_original, disciplina do cabeçalho, enunciado, assertivas, rotulos_originais, paginas, gabarito, abordagem, recursos e pendencias. Não recebe ID definitivo nem situação jurídica calculada.

O gabarito usa só o bloco Tipo 1; `*` é anulação apenas com legenda reconhecida. Posições começam em 1. Situação preliminar/definitivo vem da declaração da captação, ou do hash previamente conferido do documento. Identificação por nome é proposta conferida contra a capa; não comprova sozinha a associação semântica de documentos.

Páginas com elementos visuais/vetoriais são renderizadas integralmente em PNG, preservadas por hash em `recursos/XX/HASH` sob a saída do Digitalizador. Recursos das questões usam descritor do Organizador com `posicao:original`, ordem/pagina e descrição de página integral. Não simula recorte ou posicionamento exato de figura em assertiva. Originais PDF permanecem no Captador e são copiados ao acervo na incorporação. A reconstrução inclui o texto extraído e o acesso à representação original, com limitação explícita da apresentação visual.

`bloqueios` impede incorporação: retificações/complementos não interpretados, por exemplo. Numeração/alternativas/gabarito inválidos interrompem antes de salvar resultado. `pendencias` conserva avisos de classificação lexical, apresentação visual e demais limitações. Não equivale a revisão jurídica pendente. Classificação semântica continua não realizada; a incorporação admite tema explícito Não classificado.

O arquivo `HASH.json` contém o resultado, sem o campo resultado_id da resposta da CLI. HASH é SHA-256 de `json.dumps(resultado,sort_keys=True,ensure_ascii=False).encode()`. O Organizador confere esse hash, versão, pacote atual e arquivos de origem. Resultado v1 continua histórico, mas não é aceito pelo incorporador v2; reexecutar o extrator para obter os recursos necessários. Resultados idênticos e recursos idênticos reutilizam nomes.

`digitalizador/pipeline.py` orquestra as CLIs públicas: recepção do Captador, reserva de identidade pelo Organizador, preparação/entrega do Captador, extração e incorporação pelo Organizador. O Digitalizador não grava diretamente no acervo. O adaptador GitHub chama o mesmo pipeline. Ver [OPERACAO.md](OPERACAO.md).

Descritores são regras locais do Organizador, sem modelos. Não comprovam equivalência semântica. Compilador, agrupamentos, scores e análise de apostilas não integram este contrato.
