# Sistema de questões de concurso

Este repositório é organizado como uma empresa: cada pasta de trabalho representa um agente (funcionário), com responsabilidade, ferramentas, instruções e entregas próprias. A metáfora define a divisão de trabalho; uma pasta não cria nem executa uma IA automaticamente.

O objetivo é permitir que uma IA em CLI/harness compare os PDFs de estudo do usuário com o histórico de questões, identificando tópicos mais/menos cobrados e mudanças na cobrança ao longo do tempo. O [registro do objetivo e revisão das próximas etapas](OBJETIVO.md) distingue o que já existe das mudanças recomendadas. Essa análise ainda não está implementada.

## Módulos

| Pasta | Agente | Responsabilidade | Estado |
|---|---|---|---|
| [captador/](captador/README.md) | Captador | Recebe originais, organiza lotes e associa gabaritos | Implementado com interface no Emissor |
| [organizador/](organizador/README.md) | Organizador | Formato, armazenamento, metadados, integridade e consulta da base | CLI e testes implementados; algumas funções de escrita ainda planejadas |
| [emissor/](emissor/README.md) | Emissor | Visualização com filtros e API JSON para ferramentas próprias | Implementado |
| [digitalizador/](digitalizador/README.md) | Digitalizador | Transformar PDF, imagem ou conteúdo estruturado em material extraído, com procedência e pendências | Extrator local ENAM/FGV Tipo 1 implementado |

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
emissor/
    AGENTS.md
    README.md
    PLANEJAMENTO.md
    servidor.py
    web/
    tests/
captador/
    AGENTS.md
    README.md
    PLANEJAMENTO.md
    app.py
    tests/
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

O conteúdo que antes ficava na raiz agora está em organizador/. Após atualizar seu clone, execute os comandos dentro dessa pasta. O formato dos dados continua na versão 3: esta reorganização não altera o conteúdo dos manifestos, registros, metadados ou recursos. O Digitalizador possui extrator do perfil ENAM/FGV Tipo 1.

## Visualizar questões

Na raiz do repositório:

```sh
python emissor/servidor.py --base organizador/exemplos/base
```

Abra http://127.0.0.1:8000. Para consultar o acervo real, use `--base organizador` (ainda vazio). Todos os filtros são opcionais; sem filtros, toda a base é consultada, com paginação. Veja [Emissor](emissor/README.md) para uso da API em uma ferramenta própria.

## Receber provas e gabaritos

No mesmo servidor local, abra **Adicionar material**. Crie um lote por prova/edição/caderno, adicione a prova e depois seus gabaritos e retificações. Também é possível selecionar arquivos colocados em captador/trabalho/entrada/. Veja o [Captador](captador/README.md). A prévia permite acompanhar os documentos e processar o perfil ENAM/FGV Tipo 1, com pendências explícitas.

O Captador também mantém protocolos órgão.cargo.prova e um registro filtrável com banca, ano e outros atributos da prova. Só há encaminhamento ao Digitalizador com prova e gabarito vinculados e íntegros; a extração ENAM/FGV Tipo 1 já pode ser executada no host.

## Preparação para comparação de questões

A [abordagem da cobrança](organizador/ABORDAGEM.md) usa regras locais para gerar descritores e registra suas evidências. O Emissor apresenta os resultados e suas limitações. O [teste integrado](digitalizador/TESTE_PIPELINE_SEM_IA.md) demonstra URL → download → extração ENAM/FGV Tipo 1 → JSON intermediário, por programas no host.

## Pipeline sem IA

Na raiz:

```sh
python -m pip install -r digitalizador/requirements.txt
python emissor/servidor.py --base organizador/exemplos/base
```

Em Adicionar material: localizar links ou enviar PDFs, identificar o lote, receber prova e gabarito, encaminhar e processar. O host extrai o perfil ENAM/FGV Tipo 1, associa respostas e gera descritores por regras locais. Nenhum modelo é chamado. A prévia tem download JSON e pendências explícitas; não há incorporação automática ao acervo. Veja [Digitalizador](digitalizador/README.md).
