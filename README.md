# Base de questões de concurso

Planejamento e formato inicial de uma base local de questões, organizada em arquivos pequenos por tema. Esta entrega contém documentação e exemplos; os comandos de gestão ainda serão desenvolvidos.

## Decisões do formato

- Hierarquia: órgão → cargo → disciplina → tema.
- Pastas por órgão, cargo e disciplina; um arquivo JSONL por tema.
- Identificador: `orgao.cargo.disciplina.tema.linha`.
- A questão da linha 1 é a questão 1, sem conversão ou deslocamento.
- Cada linha contém `[situacao,enunciado,assertivas]`.
- Situação: `0` atualizada; `1` desatualizada; `2` anulada.
- Assertivas em quantidade livre, preservando a ordem.
- Inclusões ao final; nenhuma exclusão ou reordenação.
- A situação pode ser alterada, preservando a linha e seu conteúdo textual.
- O índice central lista temas e arquivos, sem enumerar questões.

## Começar localmente

```sh
git clone https://github.com/GustavoRaiser/database-de-quest-es-de-concurso.git
cd database-de-quest-es-de-concurso
```

1. Ler a [especificação](ESPECIFICACAO.md).
2. Examinar a base fictícia em [exemplos/base](exemplos/base/README.md).
3. Seguir o [plano de desenvolvimento](PLANEJAMENTO.md).

`manifesto.json`, `catalogos.json` e `indice.json` na raiz são o ponto de partida da base real, ainda vazia. A pasta `dados/` será criada no cadastro do primeiro tema. O exemplo constitui uma base independente; seus registros não devem ser importados automaticamente para a base real.

## Arquivos

| Arquivo | Papel |
|---|---|
| `manifesto.json` | Declara como interpretar a base |
| `catalogos.json` | Traduz os quatro primeiros componentes para nomes |
| `indice.json` | Localiza os arquivos dos temas |
| `dados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl` | Guarda uma questão por linha |
| `ESPECIFICACAO.md` | Define o contrato para ferramentas futuras |
| `PLANEJAMENTO.md` | Organiza a implementação local |

Os quatro primeiros códigos usam base 62 e distinguem maiúsculas de minúsculas. Antes de cadastrar dados reais, verificar se o sistema de arquivos local distingue esses nomes. A restrição está detalhada na especificação.
