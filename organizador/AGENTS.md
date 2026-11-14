# Agente: Organizador

Aplicar também ../AGENTS.md. Esta pasta concentra as ferramentas e instruções da organização definitiva da base.

## Ler antes de alterar

- README.md: uso e estado dos comandos.
- ESPECIFICACAO.md: identidade, hierarquia e registros.
- METADADOS.md: complementos, recursos e procedência.
- PLANEJAMENTO.md: recursos existentes e pendentes.
- ../CONTRATOS.md: fronteira com os demais agentes.

## Missão e limites

Manter o formato, referências, integridade, armazenamento e consulta. Não implementar OCR, extração de PDF, reconstrução de layout ou conversão de HTML nesta pasta; essas tarefas pertencem ao Digitalizador.

Código em basequestoes/, testes em tests/, exemplos fictícios em exemplos/. Os arquivos manifesto.json, catalogos.json e indice.json desta pasta iniciam a base real vazia. Não inserir dados fictícios nela.

## Invariantes

- Questões: dados/ORGAO/CARGO/DISCIPLINA/TEMA.jsonl, uma questão por linha.
- Complementos: TEMA_md.json na mesma pasta, chaves decimais em string.
- Sem pasta adicional de tema e sem ID explícito por registro principal.
- ID local: órgão.cargo.disciplina.tema.linha; linha começa em 1 e é decimal.
- Não reordenar ou excluir linhas. Código do tema e código de categoria são sensíveis a maiúsculas/minúsculas.
- Não alterar registros de questões ou versão do formato por causa de uma mudança de localização do módulo.
- Não marcar uma questão como atualizada automaticamente por vir de um PDF recente ou de uma API.
- Não abrir HTML/SVG de fontes externas como conteúdo confiável.

## Verificações

Executar a partir desta pasta:

```sh
python -m unittest discover -s tests -v
python -m basequestoes --base . validar
python -m basequestoes --base exemplos/base validar
```

Mudanças de organização física devem preservar o conteúdo dos registros, metadados e recursos. Atualizar links e comandos documentados. Bases são localizadas pelo argumento --base; não introduzir dependência do diretório raiz do Git para interpretar seus caminhos internos.

## Preparação temática

A abordagem da cobrança pertence ao Organizador; ler ABORDAGEM.md. Fornecer questão completa e apoios à IA/harness, preservar evidências, autoria, versão e vínculo ao conteúdo. Não usar palavras-chave como substituto de análise semântica. A ferramenta valida e registra perfis, mas não executa um modelo automaticamente. Não alterar categorias nem IDs como efeito da análise.
