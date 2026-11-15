# Organizador — base de questões de concurso

Base local de questões organizada em arquivos por tema, com metadados, recursos locais e procedência de importações. Formato 3; CLI em Python 3.10 ou superior, sem dependências externas.

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
cd database-de-quest-es-de-concurso/organizador
```

1. Ler a [especificação](ESPECIFICACAO.md).
2. Examinar a base fictícia em [exemplos/base](exemplos/base/README.md).
3. Seguir o [plano de desenvolvimento](PLANEJAMENTO.md).

`manifesto.json`, `catalogos.json` e `indice.json` na raiz deste módulo são o ponto de partida da base real, ainda vazia. A pasta `dados/` será criada no cadastro do primeiro tema. O exemplo constitui uma base independente; seus registros não devem ser importados automaticamente para a base real.

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

## Comandos disponíveis

Executar na pasta organizador/ (o argumento --base aponta para a base desejada):

```sh
python -m basequestoes --base exemplos/base validar
python -m basequestoes --base exemplos/base consultar N32.a2.5.y.1
python -m basequestoes --base . validar
python -m unittest discover -s tests -v
```

Guardar recurso local, sem alterar seus bytes:

```sh
python -m basequestoes --base . guardar-recurso /caminho/figura.png --mime image/png
```

O comando retorna caminho, SHA-256 e tipo MIME. Em seguida, esses campos podem compor o registro de metadados com posição e ordem de apresentação.

```sh
python -m basequestoes --base . registrar-metadados ORGAO.CARGO.DISCIPLINA.TEMA metadados-do-lote.json
python -m basequestoes --base . registrar-lote lote.json
```

`metadados-do-lote.json` contém um objeto com números de questões como chaves (por exemplo, `{"3": {"origens": [...]}}`). `lote.json` contém os objetos manifesto e relatorio. Veja o contrato e exemplos reais em [METADADOS.md](METADADOS.md) e [exemplos/base](exemplos/base/README.md). Metadados só podem referenciar questões já cadastradas; registros existentes não são sobrescritos.

Todos esses comandos preservam os arquivos em dados/. O registro de lote documenta questões existentes; ainda não extrai PDFs, acessa APIs, acrescenta questões, converte HTML ou executa OCR.

O exemplo inclui imagem SVG fictícia, conteúdo original em JSON com HTML e gabarito cujo rótulo C corresponde à segunda alternativa. Recursos são guardados sem extensão e identificados por hash e tipo MIME; nenhum HTML ou SVG é renderizado pela CLI.

## Complementos da versão 3

- `dados/.../TEMA_md.json`: arquivo auxiliar ao lado de `TEMA.jsonl`, com números de questões como chaves.
- `recursos/`: arquivos compartilhados nomeados pelo SHA-256, sem duplicar bytes.
- `importacoes/`: manifesto e relatório por lote, incluindo mapeamento e detecção de reenvio idêntico.
- [METADADOS.md](METADADOS.md): contrato, migração e limites da implementação.

A migração altera os manifestos; não altera as linhas das questões. O índice da raiz do módulo continua listando apenas temas.

## Responsabilidade deste módulo

O Organizador é responsável pelo formato, armazenamento, referências, integridade e consulta da base. Código, testes, exemplos e instruções específicos ficam nesta pasta. Leia também [AGENTS.md](AGENTS.md), a [arquitetura global](../ARQUITETURA.md) e os [contratos entre módulos](../CONTRATOS.md).

Extração de PDF, OCR e tratamento de HTML pertencem ao Digitalizador em ../digitalizador/. O Digitalizador já extrai o perfil ENAM/FGV Tipo 1 em saída intermediária, conforme sua documentação. A inclusão de questões novas a partir do contrato v2 está implementada em incorporar-extracao; alteração genérica de situações ainda é futura.

## Consulta pública para o Emissor

Na pasta organizador/:

```sh
python -m basequestoes --base exemplos/base catalogos
python -m basequestoes --base exemplos/base emitir --orgao N32 --pagina 1 --por-pagina 20
```

Filtros opcionais: --orgao, --cargo, --disciplina e --tema, com chaves completas dos catálogos. Sem filtros, inclui toda a base, paginada. A resposta inclui classificação legível e metadados. Ver [Emissor](../emissor/README.md) e o [contrato global](../CONTRATOS.md).

## Abordagem da cobrança

O Organizador prepara uma tarefa fundamentada para IA/harness e registra síntese, conhecimento exigido, recorte, conceitos, raciocínio, estrutura e evidências em abordagem nos metadados. Veja [ABORDAGEM.md](ABORDAGEM.md). Não há geração automática por modelo embutido nem agrupamento implementado.

## Processamento padrão sem IA

Os comandos descrever-questao e descrever-candidatos geram descritores por regras locais. O Digitalizador usa essa interface automaticamente. Consulte [ABORDAGEM.md](ABORDAGEM.md) para os limites e comandos. O modo de tarefa para IA/harness mencionado anteriormente permanece apenas como compatibilidade, sem integrar o fluxo padrão.

## Inclusão automática de extrações

Implementados `reservar-identidade`, `incorporar-extracao` e `recuperar`, além das operações descritas acima. Ver [contrato de incorporação](INCORPORACAO.md). O [pipeline portátil](../digitalizador/OPERACAO.md) fornece as entradas e percorre o fluxo; a gravação pertence ao Organizador. O índice continua restrito a temas; IDs existentes e bytes das linhas anteriores são preservados.
