# Compilador

Compara questões e propõe relações e grupos de semelhança. Implementado em Python 3.10+, biblioteca padrão. O modo simples funciona sem modelos; o modo semântico opcional usa IA local, conforme SEMANTICA.md. Consome um snapshot público do Organizador e escreve resultados derivados em sua própria pasta de trabalho.

A comparação considera os quatro critérios acordados: conteúdo exigido, recorte específico, raciocínio e estrutura/redação. Nesta versão, **o cálculo mede indícios lexicais**, aproveita conceitos e perfis existentes e informa dimensões ausentes. Não interpreta juridicamente o conhecimento necessário nem confirma equivalência semântica.

## Executar

Na raiz do repositório:

```sh
python compilador/app.py --base organizador analisar
python compilador/app.py --base organizador/exemplos/base comparar N32.a2.5.y.1 N32.a2.5.y.2
python compilador/app.py --base organizador/exemplos/base similares N32.a2.5.y.1
```

`analisar` busca candidatas, pontua pares, propõe grupos e salva `compilador/trabalho/HASH.json`. Retorna o resultado completo, com id e arquivo. `ultimo.json` aponta para a última compilação gravada. Repetir o mesmo conteúdo, critérios, filtros, modo e implementação produz o mesmo hash e não duplica arquivo.

`comparar` calcula qualquer par explicitamente, mesmo que ele não tenha sido selecionado pelo índice. `similares` retorna até dez pares ordenados por score; aceita `--limite N` e `--exaustivo`. Scores baixos também aparecem nessa consulta, permitindo inspecionar os indícios sem aplicar o corte dos grupos.

`analisar` e `similares` aceitam `--exaustivo`. Para 500 questões, o modo exaustivo calcula 124.750 pares; o padrão usa índice invertido para buscar até 30 candidatas por questão. Pode deixar relações de fora; o relatório informa quantos pares não foram comparados e quais buscas atingiram o limite. Pares não comparados não recebem score zero.

Todos os comandos de comparação aceitam filtros opcionais `--orgao`, `--cargo`, `--disciplina` e `--tema`, usando as chaves completas dos catálogos. Sem filtros, consulta toda a base. Não restringe por data, órgão ou disciplina implicitamente.

Para ler uma compilação arquivada:

```sh
python compilador/app.py --saida compilador/trabalho consultar HASH-DA-COMPILACAO
```

Essa consulta verifica integridade e retorna aquele snapshot; não afirma que corresponde à versão atual da base. Para atualizar, executar analisar novamente. `--saida` configura a pasta de resultados; `--criterios` permite outro JSON de configuração. A saída deve ficar fora da base do Organizador.

## Critérios e pesos iniciais

| Critério | Peso | Indicador implementado |
|---|---:|---|
| Conteúdo exigido | 40% | Similaridade de termos ponderados por TF-IDF; conceitos dos perfis; texto de conteúdo declarado, quando disponível |
| Recorte específico | 30% | Expressões de duas palavras no texto; ou comparação textual do recorte em perfis declarados |
| Raciocínio | 20% | Concordância de rótulos conhecidos nos perfis; ausente quando algum lado é indeterminado |
| Estrutura e redação | 10% | Sobreposição de sequências de três palavras em enunciado, alternativas e apoios, preservando a ordem dos campos |

TF-IDF atribui maior peso aos termos menos comuns naquele recorte de questões. Conceitos propostos também ajudam a buscar candidatas, mas não viram confirmação. A fórmula, as exceções e o contrato estão em [CONTRATO.md](CONTRATO.md).

Score vai de 0 a 100; pesos das dimensões disponíveis são renormalizados e a cobertura dos pesos é informada separadamente. Não é probabilidade de equivalência. Duas questões sem raciocínio identificado não recebem 100 nessa dimensão: ela fica nula. Os pesos/cortes são iniciais, configuráveis em criterios.json e ainda não calibrados como avaliação semântica.

Padrões: reter pares a partir de 60, propor grupos a partir de 80, exigir cobertura mínima 0,75. Grupo exige que **todos os pares internos** tenham sido comparados e superado o corte; A~B e B~C não bastam para incluir A e C. A formação é uma heurística determinística e conservadora, sem promessa de partição ótima. Os grupos são propostas, não novos temas nem novas identidades de questão.

## Entradas, saídas e limites

A entrada é `python -m basequestoes --base CAMINHO exportar`, chamada por subprocesso pelo Compilador. O snapshot contém questões, metadados, classificação e fichas de prova, com hash. Não importa código interno do Organizador e não altera suas linhas, IDs ou metadados. A exportação mantém um bloqueio temporário de escrita para obter um snapshot coerente.

Saída: nós com IDs/hashes/ocorrências, pares pontuados com evidências e avisos, grupos propostos, índice de vizinhos, fichas de prova uma vez por resultado, configuração e diagnóstico de cobertura. O resultado não replica enunciados/alternativas. Metadados e originais continuam acessíveis pelo ID no Organizador. A configuração global .gitattributes mantém LF no código/JSONL e preserva os bytes dos recursos para portabilidade. O hash do corpus e da implementação permite conferir a versão; reproduzir uma compilação antiga exige conservar a respectiva base/configuração/código.

Semelhança textual pode reunir perguntas que cobram detalhes diferentes, e textos distintos podem cobrar o mesmo conhecimento. Figuras/tabelas não são interpretadas. Negações diferentes geram aviso. Nenhum agrupamento exclui, funde ou move questões. Sem agrupamento acima do corte significa apenas ausência de vínculos retidos por esse algoritmo e recorte.

Anuladas/desatualizadas são mantidas com sua situação original. Fichas de prova e números originais preservam as ocorrências; grupos e pares não são estatísticas de cobrança. Não deduplica aplicações/cadernos nem calcula tendência ou compara PDFs de estudo. A interface visual do Emissor ainda não apresenta esses grupos; ferramentas podem consumir a CLI e o JSON.

## Integração desktop/GitHub

O pipeline `digitalizador/pipeline.py` chama o Compilador uma vez após as incorporações do pedido, analisando o acervo inteiro. Usa `--compilacoes` para configurar a saída. Se a compilação falhar, as questões já incorporadas permanecem na base; o relatório registra a falha dessa etapa e retorna execução incompleta. Pode recompilar independentemente, sem baixar ou digitalizar novamente.

No GitHub, o adaptador usa a mesma CLI e inclui `compilador/` no artefato acervo-processado. No PC, executa localmente e também funciona offline. Resultados em trabalho/ são ignorados pelo Git, incluindo compilações de provas reais. Fazer backup dos artefatos necessários antes de expirarem.

## Verificação

```sh
python -m unittest discover -s compilador/tests -v
```

Testes cobrem 500 questões, dimensões ausentes, pares distintos/idênticos, perfis, negação/visuais, grupos sem propagação transitiva, busca limitada/exaustiva, snapshot com mais de 100 questões, preservação da base e reprodutibilidade entre processos. Ver [VERIFICACAO.md](VERIFICACAO.md).

## Modo semântico adicional

Implementado o modo conjunto lexical + IA local no Compilador, com saídas separadas, registro de execução, identificação de modelos, evidências e cache. A autorização de IA limita-se ao Compilador; os demais módulos seguem por código convencional. Ver [SEMANTICA.md](SEMANTICA.md). O serviço Ollama e modelos precisam estar instalados no ambiente executor; a avaliação real dos modelos e a preparação de runner semântico permanecem pendentes.
