# Relações de semelhança — versão 1

## Entrada e identidade

Consumir a CLI pública exportar do Organizador. Snapshot v1: manifesto, itens, provas, corpus_sha256. O hash é SHA-256 do objeto sem corpus_sha256, serializado com JSON UTF-8, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(',',':'), acrescido de LF. O Compilador verifica versão e hash. O Organizador mantém .base.lock durante a exportação para impedir que escritores alterem metadados no meio do snapshot; valida a base e aplica o marcador/revisão de publicação antes de concluir a leitura.

Cada item tem id, questao ([situacao,enunciado,assertivas]), metadados opcionais e classificacao. Fichas de prova são um mapa por caminho relativo. ID continua sendo órgão.cargo.disciplina.tema.linha. Não confundir com protocolo órgão.cargo.prova ou com número original.

## Comparação lexical/1

Normalizar caixa e acentos; tokenizar letras/números. Não reordenar enunciados, assertivas ou apoios. Conteúdo usa termos não triviais, removendo a lista fixa de palavras comuns de motor.py; recorte usa bigramas por campo; redação usa trigramas por campo. Campos curtos usam seus próprios tokens. Frequência dos bigramas conta presença por campo, não quantas vezes a expressão se repete dentro de um mesmo campo.

TF-IDF: tf = 1 + ln(frequência); idf = 1 + ln((1+N)/(1+df)). Normalizar os vetores por norma euclidiana e comparar pelo cosseno. Corpus é o recorte exportado, portanto adicionar questões ou mudar filtros pode alterar scores de pares antigos. Não comparar diretamente scores de corpora diferentes como se estivessem calibrados.

Conteúdo: cosseno dos termos; quando ambos têm conceitos reconhecidos, combinar 75% desse valor com 25% da sobreposição Jaccard dos conceitos normalizados. Se ambos oferecem texto de conteúdo em perfil declarado humano/IA sem pendências, combinar o cosseno desse texto e o indicador anterior com pesos iguais. O programa só lê perfis legados de IA; não chama modelos.

Recorte: cosseno dos bigramas; se ambos oferecem recorte em perfil declarado humano/IA sem pendências, usar o cosseno dos termos desses recortes. Textos genéricos gerados por regras não são usados como declaração semântica. Marcadores Não identificado/Não determinado são tratados como ausentes.

Raciocínio: 1 para rótulos conhecidos iguais, 0 para rótulos conhecidos diferentes, nulo se um deles é indeterminado/outro/ausente. Estrutura/redação: Jaccard dos trigramas dos campos correspondentes; soma dividida pelo maior número de campos, penalizando diferença de quantidade. Conteúdo vazio de ambos não constitui evidência positiva.

Score = 100 × soma(peso × indicador disponível) / soma(pesos disponíveis). Cobertura = soma dos pesos disponíveis; não é confiança semântica. Indicadores por dimensão são expostos em 0–100 ou null; score arredondado a quatro casas. Avisos de perfis propostos, recursos não interpretados e diferenças de negação permanecem no par. A semelhança é lexical mesmo quando usa textos declarados por humanos: não interpreta seu significado.

## Candidatas e grupos

Índice invertido de termos: até termos_busca termos de maior peso por questão; listas com mais de max_postagem documentos são omitidas. Conceitos reconhecidos e baldes de texto normalizado igual também ajudam a recuperar candidatas. Ordenar por relevância e ID e limitar a vizinhos por consulta. União dos pares recuperados é comparada uma vez; há possível assimetria da busca, mas cada score de par é simétrico. Modo exaustivo ignora a seleção e compara todos os pares.

Reter pares com score >= limiar e cobertura >= cobertura_minima. A ausência no relatório pode significar não comparado, abaixo do limiar ou cobertura insuficiente; não significa score zero. O diagnóstico distingue totais comparados/não comparados e buscas truncadas. similares retorna os melhores pares efetivamente calculados, inclusive abaixo do limiar de retenção, com cobertura explícita.

Grupos: iniciar por singletons; percorrer pares por score decrescente e desempate de IDs. Unir conjuntos somente se todo par cruzado estiver retido e tiver score >= limiar_grupo. Não imputar ligações não calculadas nem usar transitividade para atestar semelhança. Só emitir grupos com dois ou mais membros. O ID do grupo é o hash da lista ordenada de membros, válido no contexto da compilação; não é ID global de assunto.

## Resultado arquivado

Objeto v1: algoritmo, implementacao_sha256, corpus_sha256, configuracao, criterios_sha256, filtros, estado proposta_lexical, limitacoes, provas, nos, pares, grupos, vizinhos e diagnostico. Implementação identifica os hashes de app.py/motor.py; configuração possui hash próprio. A lista de stopwords integra a identidade da implementação.

Nós guardam ID, hash do item exportado completo, situação, conceitos propostos e referências de ocorrência (ficha da prova/número original/páginas/URL quando presentes). O campo conteudo_sha256 do nó inclui metadados/classificação, não apenas texto. Fichas ficam no mapa provas, sem repetir banca/data no texto principal. A ordem dos nós no resultado não muda linhas da base.

Cada par contém a, b, score, cobertura, dimensoes, fontes_dimensoes, evidencias e avisos. A e B ficam em ordem lexicográfica. Evidências são termos/expressões normalizados comuns e conceitos/rótulos; IDs e hashes permitem voltar ao conteúdo original completo. Não apresenta esses termos como prova de que a alternativa está correta.

vizinhos é mapa ID → índices na lista pares, para consulta rápida de vínculos retidos. Grupos contêm lista de questões, score_minimo e estado proposta_lexical. diagnóstico informa modo, quantidade de questões, pares possíveis/comparados/não comparados/retidos, grupos, buscas truncadas e termos comuns omitidos.

Salvar como HASH.json, sendo HASH SHA-256 da serialização canônica acima do resultado inteiro. id/arquivo da resposta CLI não integram o arquivo. ultimo.json é ponteiro substituído atomicamente após salvar o resultado. Bloqueio .compilador.lock protege a publicação; resultados antigos são imutáveis e não são descartados por recompilação.

Arquivo por hash e ponteiro não substituem backup da base. consultar verifica o arquivo arquivado e não recalcula sua relação com o acervo atual. Cada compilação usa um corpus e configuração explícitos. Resultados parciais da busca são resultados completos daquele modo de busca, sem promessa de recuperar todas as semelhanças.
