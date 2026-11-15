# Análises lexical e semântica coexistentes

A autorização do usuário amplia o Compilador: ele pode usar modelos locais de IA. Captador, Digitalizador, Organizador e Emissor continuam sem inferência de modelos. Nenhum enunciado é enviado a API externa de inferência. O modo lexical permanece independente, executável e disponível em todos os resultados conjuntos.

## Plano implementado

1. Executar e salvar a análise lexical existente, sem alterar suas fórmulas.
2. Exportar novamente o snapshot público e exigir o mesmo hash de corpus para as duas análises.
3. Obter embeddings locais por trechos de cada questão e recuperar vizinhas por cosseno. Unir essas candidatas às do índice lexical. O embedding busca candidatas, sem declarar equivalência.
4. Submeter cada par ao avaliador local, pedindo pontuação separada dos quatro critérios, justificativas, citações de A/B e incertezas. Texto integral de enunciado, alternativas e apoios entra como dados. Não se pede resposta correta nem situação jurídica.
5. Validar estrutura, faixa dos scores, citações literais e cobertura. Score desconhecido fica nulo. Citações existentes não comprovam que o modelo interpretou corretamente a questão.
6. Registrar a análise semântica separadamente, associada ao ID lexical e ao hash do corpus, e propor grupos com a mesma exigência de vínculo direto entre todos os membros.
7. Manter registros de execução e cache por modelo/conteúdo/critério para distinguir análises novas, reaproveitadas e pendentes.

## Executar no desktop

Instalar e iniciar [Ollama](https://ollama.com/) no computador receptor. O programa Python usa apenas a biblioteca padrão e conversa com a API HTTP local do Ollama. Baixar os modelos uma vez, enquanto houver conexão:

```sh
ollama pull embeddinggemma
ollama pull qwen3:4b
```

Com o serviço Ollama ativo:

```sh
python compilador/app.py --base organizador semantica
```

Ou executar o pipeline completo com as duas análises:

```sh
python digitalizador/pipeline.py --pasta captador/entrada --situacao-gabarito definitivo --semantica compilador/semantica.json
```

A condição definitivo é declaração da fonte, como no pipeline anterior. No pedido JSON, a opção equivalente é `"semantica":"compilador/semantica.json"`. A configuração é opcional: sem ela, o pipeline continua lexical. O comando semantica sempre executa ambas as análises; não há substituição silenciosa.

A escolha inicial é embeddinggemma para representação multilíngue e qwen3:4b para avaliação estruturada. São modelos genéricos, ainda não calibrados em concursos jurídicos. O arquivo semantica.json permite escolher outros modelos instalados, tamanho de trecho, vizinhança e timeout. O serviço é limitado a HTTP em localhost/127.0.0.1/::1. O programa não instala modelos automaticamente.

Depois de instalados os modelos, a inferência funciona offline. Memória, disco e tempo dependem dos modelos e do tamanho do acervo; o avaliador de 4 bilhões de parâmetros pode ser demorado em CPU. O backend real não foi executado neste ambiente de desenvolvimento, que não tem Ollama/modelos. A integração foi validada com backend controlado; isso não mede a qualidade semântica dos modelos escolhidos.

## Arquivos e identificação simples

```text
compilador/trabalho/
    HASH_LEXICAL.json
    ultimo.json                         # último resultado simples
    semantica/
        HASH_SEMANTICO.json
        ultimo.json                     # último resultado IA
    registros/
        ID_DA_EXECUCAO.json              # estados das duas análises
    cache_ia/
        embeddings/HASH.json
        pares/HASH.json
```

O registro liga os dois resultados e informa início/fim, estado concluída/parcial/falha, modelos e contagens: embeddings novos/cache e pares IA novos/cache. A análise lexical recebe estado proposta_lexical; a análise IA recebe proposta_semantica_ia. Os pares semânticos conservam também score_lexical e dimensoes_lexicais, permitindo examinar divergências. Os scores não são somados automaticamente e não representam probabilidade de equivalência.

Cada resultado IA guarda nome/digest dos modelos locais, configuração, hash da implementação, hash do corpus, referência lexical e pendências. Cache de pares depende dos textos integrais A/B, modelos e hash do código semântico (inclui o prompt). Modificar entrada/modelo/critério invalida sua chave. Embeddings são reaproveitados por trecho/modelo. Os arquivos de cache têm verificação de hash e publicação atômica; corrupção não vira reaproveitamento válido.

O registro em_execucao permite identificar interrupções. Se o serviço estiver ausente, o resultado lexical fica salvo e o registro semântico indica falha. Se um par falhar, fica pendente e não entra em grupos; a execução é parcial e retorna código 2. Registros são históricos, um arquivo por execução. O ponteiro lexical nunca é substituído pelo resultado IA.

## Contexto, evidências e limites

O endpoint de embeddings usa truncate=false e trechos completos com média dos vetores normalizados. Isso evita corte silencioso, mas pode diluir detalhes entre trechos. O avaliador recebe o par integral; pares acima de 20.000 caracteres são registrados como pendentes, e respostas cujo prompt_eval_count atinge a margem do contexto de 16.384 tokens são recusadas. Não se trunca uma questão para obter um score. Imagens, PDFs e tabelas visuais não são interpretados pelo modelo textual.

Modelos podem produzir justificativas incorretas mesmo com citações literais. Temperatura zero reduz variação, sem garantir determinismo entre máquinas/versões. Cache conserva o julgamento realizado; digest de modelo identifica os pesos observados no início. Não trocar modelos enquanto uma compilação estiver rodando. Grupos continuam propostas e não alteram categorias, linhas, gabaritos ou situações da base.

## GitHub e verificação

O workflow atual de captação permanece lexical por padrão. O modo semântico exige preparar um runner com Ollama e modelos locais; publicar o código não instala esse serviço no runner. Nesta entrega não há download automático de pesos nem execução remota de IA. O mesmo comando Python pode ser usado em runner preparado ou desktop; as saídas devem ser incluídas em backup/artefato daquele ambiente.

Testes: `python -m unittest discover -s compilador/tests -v`. Cobrem coexistência, registros de falha, cache/invalidação, rejeição de citação inventada, textos extensos, estados e grupos. Antes de usar scores como critério de estudo, avaliar pares reais rotulados, incluindo sinônimos, regras/exceções próximas, negações e distratores. Essa calibração permanece pendente.

A análise semântica contém avaliacoes_ia com **todos** os pares tentados, inclusive os abaixo do limiar, origem novo/cache, score e caminho do cache; vetorizacoes_ia identifica as questões vetorizadas e seus trechos novos/reaproveitados. Assim é possível distinguir trabalho simples, trabalho IA efetivo e cache, mesmo quando nenhum grupo é formado.
