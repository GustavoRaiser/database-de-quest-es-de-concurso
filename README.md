# Sistema de questões de concurso

Este repositório é organizado como uma empresa: cada pasta de trabalho representa um agente (funcionário), com responsabilidade, ferramentas, instruções e entregas próprias. A metáfora define a divisão de trabalho; uma pasta não cria nem executa uma IA automaticamente.

## Módulos

| Pasta | Agente | Responsabilidade | Estado |
|---|---|---|---|
| [organizador/](organizador/README.md) | Organizador | Formato, armazenamento, metadados, integridade e consulta da base | CLI e testes implementados; algumas funções de escrita ainda planejadas |
| [digitalizador/](digitalizador/README.md) | Digitalizador | Transformar PDF, imagem ou conteúdo estruturado em material extraído, com procedência e pendências | Estrutura e instruções preparadas; processamento ainda não implementado |

## Estrutura

```text
AGENTS.md                # orientação para todas as IAs
ARQUITETURA.md           # mapa de responsabilidades
CONTRATOS.md             # regras de entrega entre agentes
organizador/
    AGENTS.md
    README.md
    ESPECIFICACAO.md
    METADADOS.md
    PLANEJAMENTO.md
    basequestoes/        # ferramentas do Organizador
    tests/               # testes do Organizador
    manifesto.json      # início da base real, ainda vazia
    catalogos.json
    indice.json
    exemplos/base/      # base fictícia independente
digitalizador/
    AGENTS.md
    README.md
    PLANEJAMENTO.md
```

Dentro de cada base, a estrutura continua sendo:

```text
dados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl
dados/ORGAO/CARGO/DISCIPLINA/TEMA_md.json
```

Órgão, cargo e disciplina são pastas. Tema é o nome dos dois arquivos, não uma pasta adicional. A questão é identificada pela linha decimal no arquivo de questões. Mover o módulo inteiro não altera os caminhos relativos internos nem os IDs.

## Começar

```sh
git clone https://github.com/GustavoRaiser/database-de-quest-es-de-concurso.git
cd database-de-quest-es-de-concurso/organizador
python -m basequestoes --base exemplos/base validar
python -m basequestoes --base exemplos/base consultar N32.a2.5.y.1
python -m unittest discover -s tests -v
```

Python 3.10 ou superior; o Organizador usa apenas a biblioteca padrão.

Para iniciar qualquer trabalho, ler [AGENTS.md](AGENTS.md), [ARQUITETURA.md](ARQUITETURA.md), [CONTRATOS.md](CONTRATOS.md) e as instruções do módulo escolhido. Ferramentas, testes e documentação de uma função devem ficar no módulo responsável, sem misturar extração com armazenamento definitivo.

## Mudança de localização

O conteúdo que antes ficava na raiz agora está em organizador/. Após atualizar seu clone, execute os comandos dentro dessa pasta. O formato dos dados continua na versão 3: esta reorganização não altera o conteúdo dos manifestos, registros, metadados ou recursos. O Digitalizador permanece sem código de processamento.
