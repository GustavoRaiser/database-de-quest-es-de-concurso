# Metadados, recursos e procedência — formato 2

O registro principal continua `[situacao,enunciado,assertivas]`. Nenhuma questão muda de posição ou recebe ID dentro da linha. O número decimal da linha continua identificando a questão.

## Organização

```text
manifesto.json
catalogos.json
indice.json
dados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl
metadados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl
recursos/ab/ab...hash-sha256-completo...
importacoes/identificador-do-lote/manifesto.json
importacoes/identificador-do-lote/relatorio.json
```

Não existe índice central de questões. O arquivo de metadados é opcional por tema, mas, quando uma importação usa imagens, textos de apoio ou procedência externa, esses elementos devem ser preservados antes da inclusão definitiva.

## Registro de metadados

Um objeto JSON por linha. O campo `questao` é o número decimal da linha no arquivo principal daquele tema, começando em 1. A posição do registro de metadados não tem significado. Não pode haver dois registros para a mesma questão no mesmo arquivo.

Campos reconhecidos:

| Campo | Regra |
|---|---|
| `questao` | Inteiro positivo; a questão referida deve existir |
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

O lote é gravado em pasta temporária e publicado por renomeação. Metadados são validados em conjunto antes de substituir seu arquivo. As operações usam exclusão por `.base.lock`. Após uma interrupção, conferir o estado antes de remover um bloqueio restante. Nenhum dos comandos escreve em `dados/`.

## Migrar do formato 1

1. Fazer uma cópia de segurança.
2. Alterar `versao` do manifesto para 2.
3. Acrescentar `versao_metadados: 1`, `diretorio_metadados: "metadados"`, `diretorio_recursos: "recursos"` e `diretorio_importacoes: "importacoes"`.
4. Não reescrever, mover ou ordenar arquivos de questões; catálogo e índice também permanecem iguais.
5. Executar o validador.

Pastas auxiliares vazias podem não existir. Questões antigas continuam válidas sem metadados. A CLI atual exige o manifesto v2; ferramentas antigas precisam ser atualizadas para compreender os complementos.
