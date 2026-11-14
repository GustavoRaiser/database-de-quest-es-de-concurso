# Digitalizador

Agente responsável por transformar documentos e fontes estruturadas em candidatos de questões, preservando conteúdo e procedência.

**Estado:** pasta e instruções preparadas. Ainda não existe código, CLI, OCR, extrator de PDF ou workflow de GitHub Actions neste módulo.

## Entradas e saídas previstas

| Entrada | Entrega esperada |
|---|---|
| PDF com texto | Questões, alternativas, textos de apoio, páginas e pendências |
| Imagem/PDF digitalizado | Extração por OCR com indicação das dúvidas |
| HTML/JSON de API | Conteúdo estruturado com preservação do original e recursos |
| Gabarito da mesma prova/caderno | Correspondência com números e rótulos originais |

As saídas são intermediárias. O Digitalizador não atribui IDs locais por linha nem grava questões no Organizador.

## Onde começar

1. Ler [AGENTS.md](AGENTS.md).
2. Ler a [arquitetura global](../ARQUITETURA.md) e os [contratos](../CONTRATOS.md).
3. Seguir [PLANEJAMENTO.md](PLANEJAMENTO.md).
4. Consultar o formato de destino em [organizador/ESPECIFICACAO.md](../organizador/ESPECIFICACAO.md) e [organizador/METADADOS.md](../organizador/METADADOS.md).

Quando houver implementação, código, testes, dependências, ferramentas, exemplos de entrada e instruções de execução ficarão dentro desta pasta. O primeiro alvo previsto é um caderno oficial do ENAM/FGV acompanhado do gabarito correspondente; nenhum documento foi importado nesta reorganização.
