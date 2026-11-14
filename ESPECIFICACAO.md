# Especificação do formato — versão 2

A versão 2 mantém os registros e IDs anteriores e acrescenta a camada definida em [METADADOS.md](METADADOS.md). Ela contém o contrato de recursos, HTML original, gabaritos e procedência.

## 1. Escopo

Armazenar questões para consulta e processamento futuro, com baixo custo estrutural. Os arquivos são a fonte oficial; nenhuma aplicação ou banco de dados é necessário para interpretá-los.

Os caminhos citados são relativos à pasta que contém o manifesto da respectiva base. A base em `exemplos/base/` é independente da base da raiz.

## 2. Identificação e localização

Identificador completo:

```text
ORGAO.CARGO.DISCIPLINA.TEMA.LINHA
N32.a2.5.y.12
```

O exemplo indica a linha física 12 de `dados/N32/a2/5/y.jsonl`.

Os quatro primeiros segmentos usam o alfabeto ordenado de base 62:

```text
0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
```

A geração segue 0…9, A…Z, a…z, 10, 11…; não utiliza zeros à esquerda, exceto o próprio código 0. Os códigos são strings, distinguem maiúsculas de minúsculas, não são reutilizados e são únicos dentro do pai. Órgãos são únicos na base; cargos dentro do órgão; disciplinas dentro do cargo; temas dentro da disciplina.

O quinto segmento é um inteiro decimal positivo sem zeros à esquerda, igual ao número da linha. Não usa base 62: linha 10 é questão 10. Não há ID explícito no registro.

Somente códigos válidos podem compor caminhos; nomes legíveis e entradas contendo barras, pontos ou travessia de diretórios não podem ser usados como códigos.

### Compatibilidade de pastas

Base 62 exige armazenamento que distinga maiúsculas de minúsculas. Em sistemas que tratam A e a como o mesmo nome, a implementação deve recusar gravações ou utilizar um volume compatível. Não converter códigos para minúsculas nem trocar o alfabeto silenciosamente. Uma alternativa em base 36 exigirá uma decisão explícita antes da carga real e atualização do manifesto.

## 3. Arquivos de questões

Caminho obrigatório:

```text
dados/{orgao}/{cargo}/{disciplina}/{tema}.jsonl
```

Cada linha é um array JSON de exatamente três campos:

| Posição | Tipo | Significado |
|---|---|---|
| 0 | Inteiro 0, 1 ou 2 | Situação atual |
| 1 | String | Enunciado |
| 2 | Array de strings | Assertivas em ordem |

Situações: 0 = atualizada; 1 = desatualizada; 2 = anulada. Booleanos não são códigos de situação. “Atualizada” é uma classificação atribuída por quem cadastra, não uma conclusão automática de validação jurídica.

Exemplo de uma linha:

```json
[0,"Assinale a alternativa correta.",["Primeira assertiva.","Segunda assertiva."]]
```

A quantidade de assertivas é livre, inclusive zero. Não há campos de gabarito, fonte, data, banca ou tipo de questão na linha principal; os complementos pertencem aos metadados da versão 2. Ferramentas não devem inferir esses dados a partir da situação ou da posição das assertivas.

### Serialização e linhas

- UTF-8 sem BOM, com terminadores LF.
- Uma questão por linha física, sem cabeçalhos, comentários ou linhas vazias.
- O arquivo não contém um array externo envolvendo os registros.
- Textos com quebras de linha usam escapes JSON, como `\n`, dentro da mesma linha física.
- Aspas e barras invertidas são escapadas por um serializador JSON.
- `;;` não é delimitador deste formato e pode aparecer normalmente no texto.
- Preservar acentos, pontuação, espaços e ordem das assertivas.
- Arquivo sem questões tem zero bytes; não contém uma linha vazia.
- Cada registro gravado termina com LF. O LF final não conta como questão adicional.
- Não formatar um registro em várias linhas.

## 4. Preservação e alterações

Inclusões acrescentam registros somente ao final. Nenhuma operação pode apagar questões, inserir no meio, ordenar, compactar lacunas ou alterar sua posição. Anulação e desatualização não removem registros.

É permitido atualizar apenas o campo de situação de uma questão existente, mantendo os demais campos e sua linha. Não há arquivo de eventos nem histórico de situações no formato atual. O Git pode registrar revisões, mas não integra o contrato de leitura da base.

Correções de enunciado ou assertivas ainda não têm procedimento definido e devem ser recusadas pela ferramenta inicial. Não alterar o texto silenciosamente.

Renomear uma categoria no catálogo preserva seu código. Mover registros ou renomear códigos e caminhos altera sua identidade; essas operações continuam fora do escopo implementado.

Para gravar: validar primeiro, obter exclusividade por arquivo e impedir que inclusões e atualizações concorrentes percam dados. Atualizações de situação devem escrever um arquivo temporário no mesmo volume, verificar o resultado e substituí-lo com segurança. Não truncar o original antes de concluir a nova gravação. Uma operação sobre catálogo e índice também precisa prever recuperação de falhas.

## 5. Catálogos

`catalogos.json` contém quatro objetos:

```json
{
  "orgaos": {"N32":"Órgão fictício"},
  "cargos": {"N32.a2":"Analista fictício"},
  "disciplinas": {"N32.a2.5":"Disciplina de exemplo"},
  "temas": {"N32.a2.5.y":"Tema de exemplo"}
}
```

Cada chave usa o caminho completo até aquele nível. Cada valor é uma string não vazia. Todo filho deve ter seu pai cadastrado. Nomes iguais não provam que duas categorias são a mesma; a ferramenta deve apresentar possíveis repetições antes de cadastrar outra.

## 6. Índice

`indice.json` contém:

```json
{"temas":{"N32.a2.5.y":"dados/N32/a2/5/y.jsonl"}}
```

O índice termina no tema: não lista IDs de questões, linhas, intervalos ou contagens obrigatórias. Cada caminho deve corresponder exatamente aos quatro códigos da chave e apontar para um arquivo existente. Temas sem questões podem apontar para arquivos vazios.

O índice é derivado: pode ser reconstruído percorrendo os arquivos válidos em dados/. Arquivos sem catálogo correspondente devem ser relatados como inconsistências; reconstruir o índice não deve inventar nomes, apagar dados ou ocultar problemas.

## 7. Manifesto

`manifesto.json` declara formato, versão, codificação, campos, situações, regras dos IDs e localização dos arquivos. A versão atual é 2; o contrato auxiliar é declarado por versao_metadados: 1. Uma ferramenta deve rejeitar versões ou regras que não suporte, sem tentar adivinhar sua interpretação.

O alfabeto configurado identifica a base 62 acordada; não autoriza alterar códigos existentes. Qualquer evolução incompatível exige um procedimento de migração e revisão da versão.

## 8. Consulta e importação

Consulta por ID:

1. Separar exatamente cinco componentes e validá-los.
2. Localizar o tema pelos quatro primeiros componentes no índice.
3. Ler o arquivo até a linha decimal solicitada.
4. Interpretar o array JSON e retornar situação, enunciado e assertivas.
5. Se o tema ou a linha não existir, informar “não encontrado”, sem criar registro.

Consultar por nome exige primeiro buscar no catálogo. Listar um tema consiste em percorrer o arquivo e associar cada linha ao seu número natural.

Importação recebe o tema de destino e registros no formato de três campos. Deve validar o lote antes de acrescentá-lo e retornar o intervalo de linhas efetivamente cadastrado. Repetir uma importação pode duplicar conteúdo: detecção de repetição deve avisar, sem excluir ou fundir questões automaticamente. IDs fornecidos por outra base não devem ser preservados implicitamente ao anexar registros.

O formato com `;;` não é uma entrada oficial do formato atual. Um adaptador futuro deverá definir suas regras de escape antes de aceitá-lo.

## 9. Validação e diagnósticos

Conferir manifesto, tipos, situação, códigos, vínculos entre pais e filhos, catálogo, índice, caminhos e cada linha JSONL. Relatar arquivo, linha quando aplicável e motivo.

Rejeitar JSON com chaves duplicadas nos arquivos de controle. Em JSONL, rejeitar registros que não sejam arrays de três campos, situações fora do conjunto permitido, enunciados não textuais e assertivas que não sejam uma lista de strings.

Não pular linhas inválidas: elas ocupam posições e pular sua contagem alteraria a identificação. Não reparar arquivos apagando linhas vazias. A ferramenta deve interromper a operação de gravação e exigir diagnóstico.

## 10. Metadados e recursos

Consulte [METADADOS.md](METADADOS.md). Arquivos de metadados usam o mesmo caminho de tema em metadados/, com número explícito da questão em cada objeto. Recursos são locais, nomeados pelo SHA-256 completo. Lotes guardam manifesto e relatório com correspondência entre número original e ID local. O índice central continua restrito aos temas.

## 11. Limites e extensões

Arquivos por tema facilitam a localização, mas não garantem tamanho máximo. Consulta por linha ainda percorre os bytes anteriores, salvo uso de índice auxiliar.

Índices de posições em bytes são opcionais e reconstruíveis. Uma mudança de situação pode mudar o tamanho em bytes do registro; invalidar ou reconstruir esses índices após qualquer gravação.

Não dividir fisicamente um tema já cadastrado sem especificar antes como preservar sua numeração. Essa extensão não integra a versão 2.

Manter JSONL sem compressão durante a edição local. Backups podem ser comprimidos. Medir volume e acesso com dados reais antes de acrescentar compressão de trabalho, banco de dados ou deduplicação.
