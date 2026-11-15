# Operação atual: descritores por regras, sem IA

A partir da decisão do usuário, o fluxo padrão executa no host e não chama IA. Os comandos de tarefas para harness descritos historicamente abaixo são legados opcionais; não são usados pelo Digitalizador.

Na pasta organizador/:

```sh
python -m basequestoes --base exemplos/base descrever-questao N32.a2.5.y.1
python -m basequestoes --base exemplos/base descrever-questao N32.a2.5.y.1 --salvar
```

--salvar exige metadados de origem já existentes. --substituir preserva a descrição anterior no histórico. O campo geracao aceita regras, além de ia/humano para leitura e compatibilidade dos registros anteriores.

A CLI descrever-candidatos recebe uma lista JSON pela entrada padrão e retorna abordagens, uma por candidato. Cada candidato contém enunciado e listas opcionais assertivas/textos_apoio/recursos. Essa é a interface usada pelo Digitalizador, sem importar implementações internas.

O vocabulário em basequestoes/regras.json é inicial, pequeno e auditável. Comparações ignoram caixa e acentos e respeitam limites de palavras. São registradas as regras acionadas, evidências literais, versão e hash da configuração. Raciocínio só recebe um rótulo quando um comando textual conhecido é reconhecido; nos demais casos é indeterminado. Sem correspondência retorna Não identificado. O campo conteudo_exigido explicita que não houve determinação semântica.

Ocorrência lexical em uma alternativa pode ser um distrator. Não usar o perfil como prova de equivalência nem como classificação temática confirmada. O perfil registra pendências e é mostrado como proposta. Não há modelo embutido, custo de API, resposta correta inferida ou atualização jurídica automática.

---

## Histórico do contrato de perfis e modo harness

# Abordagem da cobrança — critério 1

Etapa do Organizador que prepara uma análise por IA/harness e registra o que cada questão exige. O registro permanece em TEMA_md.json, na chave da questão, sob abordagem. A linha JSONL e o ID permanecem iguais. A extensão é opcional e compatível com as bases no formato 3 existentes.

## Fluxo executável

Na pasta organizador/:

```sh
python -m basequestoes --base exemplos/base preparar-abordagem N32.a2.5.y.1 > tarefa.json
```

O comando produz instruções, identificação, classificação atual, enunciado, todas as assertivas, textos de apoio, recursos, hash do contexto e formato de resposta. A IA do CLI/harness recebe essa tarefa e produz a análise. Não há chamada automática a provedor de IA, custo de API ou geração por heurística de palavras-chave. O harness deve executar o modelo de sua escolha e registrar sua identificação real.

A resposta deve ser envolvida por um mapa com o número da questão como chave: {"1": PERFIL}. Salve esse JSON em resposta.json e execute:

```sh
python -m basequestoes --base exemplos/base registrar-abordagens N32.a2.5.y resposta.json
python -m basequestoes --base exemplos/base consultar N32.a2.5.y.1
```

Cada questão precisa ter metadados de origem cadastrados antes de receber abordagem. Não inventar procedência para preencher essa exigência. O registro pode receber várias respostas do mesmo tema em uma operação; todas são verificadas antes da gravação.

Para refazer uma análise:

```sh
python -m basequestoes --base exemplos/base registrar-abordagens N32.a2.5.y resposta.json --substituir
```

A anterior é preservada em historico_abordagens. A gravação usa bloqueio e substituição atômica. As demais informações, incluindo origem e gabarito, são preservadas. registrado_em é inserido pela ferramenta.

## Campos do perfil

| Campo | Conteúdo |
|---|---|
| versao_criterio | Inteiro 1 |
| base_sha256 | Hash emitido na tarefa, copiado na resposta |
| sintese | Descrição concisa do que foi abordado |
| conteudo_exigido | Conhecimento necessário para resolver |
| recorte_especifico | Detalhe daquele conhecimento que está sendo cobrado |
| conceitos | Lista não vazia, sem termos repetidos |
| raciocinio | reconhecer_definicao, identificar_regra, aplicar_regra, identificar_excecao, comparar, interpretar, calcular, outro ou indeterminado |
| estrutura | Como o enunciado e as alternativas apresentam o problema |
| evidencias | Trechos exatos do enunciado, assertivas ou textos de apoio |
| geracao | ia ou humano |
| autor | Identificação do responsável/harness |
| modelo | Obrigatório quando geracao é ia |
| estado | proposta ou declarada; não é a situação jurídica da questão |
| pendencias | Lista de dúvidas e recursos não interpretados; pode ser vazia |

Evidência de enunciado: {"campo":"enunciado","trecho":"texto literal"}. Para assertiva ou texto_apoio, acrescentar indice começando em 1. Índices inexistentes e trechos ausentes são recusados. A ferramenta verifica existência dos trechos, não se eles sustentam corretamente a interpretação semântica.

O hash inclui enunciado, assertivas, textos de apoio e descritores dos recursos, com serialização canônica. Não inclui situação, data da coleta ou gabarito. Uma mudança apenas de situação não invalida o perfil; alteração de conteúdo faz a validação apontar incompatibilidade. O histórico conserva registros anteriores como snapshots, sem reinterpretá-los como perfis atuais.

## Uso pelo Compilador

Os perfis oferecem conteúdo exigido, recorte, raciocínio e estrutura para buscar candidatas. O texto completo continua sendo a evidência final para comparar pares. Pendências precisam acompanhar o consumo; não transformar uma descrição incerta em equivalência confirmada. A ausência de perfil não significa ausência de assunto.

Agrupamento, embeddings, score, comparação entre pares e propagação de similaridade ainda não estão implementados. O critério 1 também não gera automaticamente disciplina/tema nem move questões. Essa etapa não exige revisão jurídica obrigatória e não determina resposta correta.

## Exibição e avaliação de PDF

O Emissor exibe a síntese, conceitos, raciocínio e pendências em “O que esta questão aborda”, além dos metadados completos. Veja [a avaliação do fluxo de PDF](../digitalizador/AVALIACAO_PDF.md) para os limites entre recepção de documento e análise de uma questão já estruturada.
