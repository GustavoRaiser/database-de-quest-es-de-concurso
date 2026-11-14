# Avaliação: é possível processar um PDF enviado pela interface?

Avaliação do repositório após a implementação da abordagem da cobrança. A conclusão distingue os passos executáveis hoje dos ainda pendentes.

| Etapa | Estado e evidência |
|---|---|
| Selecionar PDF no navegador e enviar | Implementado no Emissor/Captador, com limite de 15 MiB por arquivo |
| Preservar os bytes originais, hash e identificação | Implementado; teste HTTP envia PDFs sintéticos válidos de uma página e confere os bytes preservados |
| Associar prova e gabarito | Implementado, por declaração do usuário, com validação do vínculo e integridade |
| Encaminhar lote completo | Implementado; teste confere pacote criado em encaminhamentos/ e estado aguardando_digitalizador |
| Extrair texto/layout do PDF | Não implementado: digitalizador/ ainda não tem extrator ou dependências |
| Separar questões, alternativas, páginas e apoios | Não implementado |
| Interpretar e associar respostas do gabarito | Não implementado |
| Cadastrar categorias e acrescentar questões ao acervo por comando | Ainda planejado no Organizador |
| Preparar análise e registrar abordagem de questão já estruturada | Implementado no Organizador; a geração semântica é feita por IA/harness externo ao programa |
| Agrupar questões e calcular similaridade | Não implementado |

Portanto, o upload funciona até a fila documental. O repositório sozinho ainda não transforma um PDF enviado em questões pesquisáveis ou perfis semânticos automaticamente. Upload não equivale a extração. O teste não mede qualidade de OCR ou de interpretação de provas reais.

Para uma prova, manter a regra de envio somente com prova e gabarito, ambos íntegros e vinculados. Para PDF de estudo, o objetivo é outro: precisará de entrada e contrato separados, sem fingir que é uma prova ou exigir gabarito de material didático.

## Como reproduzir a parte existente

Na raiz:

```sh
python emissor/servidor.py --base organizador/exemplos/base
```

Abrir http://127.0.0.1:8000 → Adicionar material. Identificar prova/caderno, enviar o PDF da prova e o PDF do gabarito, selecionar o gabarito e encaminhar. A interface mostrará a fila, sem declarar a extração concluída.

O teste automatizado dessa recepção está em emissor/tests/test_emissor.py, no caso test_upload_pdf_completo_ate_fila. Todos os arquivos do teste são fictícios e temporários. Nenhum documento real foi importado ou analisado para esta avaliação.

## Próximo passo técnico

Implementar um Digitalizador inicial para PDFs com texto selecionável, com contrato intermediário e testes de colunas, continuidade entre páginas, alternativas, textos de apoio, imagens e gabarito/caderno. PDFs digitalizados como imagens exigirão OCR e tratamento de dúvidas. Em seguida, implementar a incorporação pelo Organizador. A preparação de abordagem poderá então receber cada questão estruturada, sem tentar analisar o PDF bruto dentro do Organizador.

Não foram instaladas dependências de PDF nem criado um extrator nesta entrega: o pedido foi avaliar essa possibilidade após implementar a lógica de abordagem.
