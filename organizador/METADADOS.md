# Metadados, recursos e procedência — formato 3

O registro principal continua `[situacao,enunciado,assertivas]`. Nenhuma questão muda de posição ou recebe ID dentro da linha. O número decimal da linha continua identificando a questão.

## Organização

```text
manifesto.json
catalogos.json
indice.json
dados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl
dados/ORGAO/CARGO/DISCIPLINA/TEMA_md.json
recursos/ab/ab...hash-sha256-completo...
importacoes/identificador-do-lote/manifesto.json
importacoes/identificador-do-lote/relatorio.json
```

Não existe índice central de questões. O arquivo de metadados é opcional por tema, mas, quando uma importação usa imagens, textos de apoio ou procedência externa, esses elementos devem ser preservados antes da inclusão definitiva.

## Registro de metadados

Um objeto JSON por arquivo, com números decimais das questões como chaves: `{"3": {"origens": [...]}, "80": {"origens": [...]}}`. Cada chave corresponde à linha do arquivo TEMA.jsonl, começando em 1, sem zeros à esquerda. Não há campo `questao` nos valores nem correspondência entre linhas dos dois arquivos. Não há posições vazias para questões sem complementos. O arquivo pode ser formatado em várias linhas. Chaves duplicadas são recusadas.

Ao reconstruir uma questão, procurar a chave correspondente em TEMA_md.json. Se o arquivo ou a chave não existir, retornar metadados nulos. A ausência de metadados não comprova que uma importação foi completa.

Campos reconhecidos:

| Campo | Regra |
|---|---|
| Chave do objeto | Número decimal positivo em string; a questão referida deve existir |
| `origens` | Lista não vazia de origens |
| `gabarito` | Opcional; ausência significa informação não registrada |
| `textos_apoio` | Lista opcional de strings em texto simples, na ordem original |
| `recursos` | Lista opcional de recursos locais com posição de apresentação |

### Origens

Cada origem exige `fonte`, `coletado_em` em AAAA-MM-DD e ao menos um dos seguintes: `id_externo`, `url` ou `documento` (descritor de recurso local). Campos adicionais de procedência podem incluir `numero_original` (string), `prova` (string), `pagina` (inteiro positivo), `tipo_caderno`, `banca`, `ano` e `url`.

Pode haver várias origens para a mesma questão. Não deduzir igualdade de questões só porque os números originais coincidem. O identificador externo não substitui o ID local.

### Gabarito

```json
{"situacao":"definitivo","alternativas_corretas":[2],"rotulos_originais":["C"]}
```

`alternativas_corretas` usa posições começando em 1 na lista de assertivas local. O exemplo marca a segunda assertiva, cujo rótulo original era C. Letras originais não determinam a posição local. Listas permitem mais de uma resposta correta e não podem conter posições repetidas ou inexistentes.

Situações possíveis:

- `ausente`: lista de respostas vazia; não há resposta conhecida.
- `preliminar`: uma ou mais posições conhecidas, ainda preliminares.
- `definitivo`: uma ou mais posições conhecidas, definitivas na fonte.
- `anulado`: lista vazia e situação 2 no registro principal.

Uma questão anulada pode manter um gabarito anterior documentado como preliminar/definitivo; a situação 2 impede tratá-lo como resposta vigente. A falta de gabarito não indica anulação. Não inferir atualização jurídica a partir do gabarito.

## Recursos locais

Todo recurso usa este descritor básico:

```json
{"arquivo":"recursos/ab/ab...64-caracteres...","sha256":"ab...64-caracteres...","tipo_mime":"image/png"}
```

O nome real é o SHA-256 completo dos bytes, sem extensão. Os dois primeiros caracteres do hash definem a pasta. O mesmo conteúdo é guardado uma vez; o tipo MIME é declarado no descritor e deve ser conferido pela aplicação que exibir o arquivo. Hash confirma integridade, não segurança nem autenticidade da fonte.

`guardar-recurso` copia um arquivo local sem modificar os bytes e devolve o descritor para usar nos metadados. Ele não baixa URLs e não executa arquivos. As URLs originais podem ser preservadas como campo adicional no descritor, sem substituir a cópia local.

Para vincular à apresentação, acrescentar:

| Campo | Regra |
|---|---|
| `posicao` | `antes_enunciado`, `apos_enunciado`, `assertiva`, `texto_apoio` ou `original` |
| `indice` | Posição começando em 1; obrigatório apenas para assertiva/texto de apoio |
| `ordem` | Inteiro positivo para ordenar recursos no mesmo destino |
| `descricao` | Texto opcional; não inventar descrição como se viesse da fonte |

Não repetir a combinação posição, índice e ordem. `original` é material para conferência, não um elemento que deve ser apresentado automaticamente.

Nesta versão, o vínculo localiza recursos antes/depois do enunciado ou junto a uma assertiva/texto de apoio. Não define inserção em um caractere específico. Quando a posição exata dentro do texto importa, conservar a representação original e deixar a importação pendente até definir uma representação fiel.

## HTML e textos associados

Guardar a resposta original da API em recurso `application/json` ou o HTML original em `text/html`, com posição `original`. Preservar enunciado, alternativas e textos associados originais para poder auditar a conversão.

O arquivo principal é a representação em texto simples. Textos de apoio comuns podem ficar nos metadados para não serem repetidos; uma aplicação deve apresentá-los antes da questão. Importadores não podem omitir esses textos ou imagens só porque não cabem nos três campos principais.

O programa atual preserva os arquivos e valida referências. Não converte HTML, renderiza imagens, faz OCR ou sanitiza HTML. Antes de construir uma tela, definir uma política de sanitização por lista permitida; nunca inserir HTML ou SVG de origem externa diretamente na página. Fórmulas, tabelas e estilos semanticamente importantes exigem tratamento específico, não remoção indiscriminada de tags.

## Registro de lote concluído

`registrar-lote` registra a procedência de questões **já existentes**. Não é um importador de PDF nem uma operação que acrescenta questões. Recebe um JSON com `manifesto` e `relatorio`.

O manifesto contém:

- `id`: letras minúsculas, números, hífen ou sublinhado; começa com letra/número; até 80 caracteres.
- `fonte`, `coletado_em` e `versao_importador`: obrigatórios.
- `documentos`: descritores locais com hash e tipo MIME, acrescidos da URL original.
- `fingerprint`: calculado pela ferramenta na gravação, não fornecido como garantia pelo usuário.

O relatório contém:

```json
{
  "mapeamento": [{"numero_original":"41","questao_id":"N32.a2.5.y.1"}],
  "pendencias": []
}
```

Cada número original e destino aparecem uma vez por lote. Usar um lote por prova/caderno. Todas as questões devem existir. Qualquer pendência impede registrar o lote como concluído.

A impressão digital combina fonte, hashes dos documentos e números originais, independentemente do nome do lote, data e destinos locais. Reenviar esse mesmo conjunto com outro nome é recusado. Isso detecta lotes idênticos, não qualquer questão semanticamente repetida nem sobreposição parcial de lotes. Um futuro importador deverá conferir lotes anteriores **antes** de acrescentar questões.

O lote é gravado em pasta temporária e publicado por renomeação. Metadados são validados em conjunto antes de substituir seu arquivo. As operações usam exclusão por `.base.lock`. Após uma interrupção, conferir o estado antes de remover um bloqueio restante. Esses comandos auxiliares não acrescentam linhas em `dados/`. A inclusão via incorporar-extracao é documentada separadamente em INCORPORACAO.md.

## Migração dos formatos anteriores

A versão 3 usa `versao_metadados: 2`. A mudança é incompatível com o armazenamento auxiliar da versão 2, embora as linhas das questões permaneçam intactas. A CLI exige o manifesto v3.

Para migrar uma base v2:

1. Fazer backup e suspender gravações durante a conversão.
2. Para cada arquivo metadados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl, converter os objetos em um mapa. Retirar o campo questao de cada registro e usar seu valor decimal como chave em string. Recusar registros duplicados antes de converter.
3. Salvar o mapa em dados/ORGAO/CARGO/DISCIPLINA/TEMA_md.json. Não sobrescrever um arquivo já existente sem comparar os conteúdos.
4. No manifesto, definir versao: 3 e versao_metadados: 2; remover diretorio_metadados; acrescentar caminho_metadados: "dados/{orgao}/{cargo}/{disciplina}/{tema}_md.json". Preservar os diretórios recursos e importacoes.
5. Conferir a equivalência dos registros convertidos e retirar os arquivos auxiliares antigos da base ativa, preservando o backup. O validador recusa arquivos JSONL restantes na antiga pasta metadados/.
6. Validar a base e comparar os hashes dos arquivos de questões antes/depois. Eles não devem mudar. Catálogo, índice, recursos e registros de lotes permanecem iguais.

Para uma base v1 sem complementos, atualizar o manifesto para a versão 3, acrescentar versao_metadados: 2, caminho_metadados e os diretórios recursos/importacoes conforme o manifesto de exemplo. Não alterar arquivos de questões.

Os manifestos e o exemplo deste repositório já estão migrados. Não há comando automático de migração de bases externas nesta entrega.

## Abordagem da cobrança

Campo opcional abordagem, com critério versionado, hash do contexto, síntese, conteúdo exigido, recorte específico, conceitos, raciocínio, estrutura, evidências e autoria. O contrato e os comandos estão em [ABORDAGEM.md](ABORDAGEM.md). Reanálises explícitas preservam historico_abordagens. A extensão é compatível com o formato 3: registros anteriores sem perfil permanecem válidos.

## Incorporação e ficha de prova

`incorporar-extracao` acrescenta questões e metadados em uma publicação recuperável, com validação prévia e preservação de IDs. `origens[].ficha_prova` aponta para `provas/ORGAO/CARGO/SHA_PROVA.json`; a ficha guarda identificação detalhada, documentos locais por hash e mapeamento para números originais. O validador confere referências locais e grupo da ficha. Detalhes em [INCORPORACAO.md](INCORPORACAO.md). Extensão auxiliar compatível com o formato 3; bases antigas sem esse campo continuam válidas.

Para extrações v2 ENAM, o original PDF e páginas integrais em PNG permanecem disponíveis. Recursos com posição original são material para conferência e não simulam inserção da figura no texto. Classificação temática não confirmada fica em Não classificado; avisos não são apagados para registrar um lote tecnicamente incorporado.
