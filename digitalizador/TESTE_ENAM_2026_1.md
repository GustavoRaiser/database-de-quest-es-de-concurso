# Teste real de URL — ENAM 2026.1

**Registro histórico:** o diagnóstico abaixo foi seguido pela implementação integrada, documentada em [TESTE_PIPELINE_SEM_IA.md](TESTE_PIPELINE_SEM_IA.md). A indicação de “não implementado” descreve apenas o estado na execução deste diagnóstico inicial.

Executado em 15/11/2026, a pedido do usuário. Este relatório registra um diagnóstico; não implementa um extrator nem altera o acervo definitivo.

## Fonte e seleção

A [página indicada](https://www.qconcursos.com/questoes-de-concursos/provas?by_institute%5B%5D=10726) retornou uma listagem de seis provas do ENAM. Foi selecionada a entrada ENAM 2026.1, com aplicação informada em 07/06/2026, banca FGV. Trata-se de página HTML de listagem, não de um PDF direto.

Documentos acessados:

- [Prova](https://arquivos.qconcursos.com/prova/arquivo_prova/152734/fgv-2026-enam-exame-nacional-da-magistratura-enam-2026-1-prova.pdf): 599.159 bytes, 32 páginas, Tipo 1.
- [Gabarito](https://arquivos.qconcursos.com/prova/arquivo_gabarito/152734/fgv-2026-enam-exame-nacional-da-magistratura-enam-2026-1-gabarito.pdf): 127.365 bytes, 2 páginas, vários tipos de caderno.
- [Gabarito definitivo na FGV](https://conhecimento.fgv.br/sites/default/files/concursos/enam-exame-nacional-de-magistratura-2026.1.pdf): baixado separadamente para comparação; seu SHA-256 coincide com o arquivo do Qconcursos.

SHA-256 da prova: 31a6228c7f2ec52358fffb1f6add267ed075ead17d5c3ad37a500d465d084aa4.

SHA-256 de ambos os arquivos de gabarito: 81c1cbfbcab8df8d6ba0cd2f1ac2950b16cefe6147ed6490af8799b14dbfbba7.

O link adicional de alterações da listagem retornou HTTP 403 na ferramenta de leitura. Não foi incorporado ao teste. A igualdade com o PDF definitivo da FGV foi verificada para o gabarito efetivamente recebido.

## Teste do Captador existente

A descoberta dos links e os downloads foram feitos pelo agente de teste, fora do programa. O Captador ainda não resolve páginas HTML nem baixa URLs automaticamente.

Com os PDFs locais, foram usadas as operações públicas criar, anexar e encaminhar do Captador, por CLI, em pasta de trabalho isolada:

1. Registro de prova/edição/caderno, banca, ano e data de aplicação.
2. Recepção da prova pela entrada por pasta, com URL de origem registrada.
3. Tentativa de encaminhamento sem gabarito: recusada. Estado aguardando_gabarito.
4. Recepção do gabarito definitivo, vinculado ao hash da prova.
5. Encaminhamento completo: aceito e pacote registrado em encaminhamentos/. Estado aguardando_digitalizador.

O protocolo 0.0.0 foi reservado apenas nesse ambiente isolado de diagnóstico; não define os códigos reais de órgão/cargo do acervo. Não foram criadas questões na base definitiva. Arquivos de trabalho estão sob captador/trabalho/teste-enam-url/, ignorados pelo Git. PDFs e textos integrais não foram publicados junto deste relatório.

## Diagnóstico externo de extração

Foram utilizadas bibliotecas já disponíveis no ambiente de execução (pdfplumber, pypdf e PyMuPDF), por comandos de diagnóstico fora do código do projeto. Essas dependências não estão configuradas no Digitalizador do repositório.

A prova contém texto extraível. O experimento percorreu as páginas de questões por colunas, retirou cabeçalhos/rodapés conhecidos, separou os marcadores numéricos e as alternativas e selecionou o bloco Tipo 1 do gabarito.

| Verificação estrutural | Resultado |
|---|---:|
| Questões numeradas sequencialmente | 80, de 1 a 80 |
| Alternativas identificadas | 400 |
| Questões com rótulos A, B, C, D e E em ordem | 80 |
| Enunciados ou alternativas vazios | 0 |
| Entradas de gabarito associadas pelo número original | 80 |
| Questões marcadas como anuladas no gabarito Tipo 1 | 1: número 42 |

Foram reconhecidos oito cabeçalhos de disciplinas. A distribuição estrutural encontrada foi: Constitucional 16, Administrativo 10, Noções Gerais de Direito/Formação Humanística 6, Direitos Humanos 6, Processual Civil 12, Civil 12, Empresarial 6 e Penal 12.

Existem imagens embutidas no documento, incluindo imagens repetidas em várias páginas. A extração textual e a contagem de alternativas não constituem validação da preservação de todos os elementos visuais. Não houve conferência visual integral das 80 questões, classificação em temas nem geração de abordagem por IA. Não foi atribuída automaticamente situação jurídica atualizada às questões.

## Conclusão e próximo trabalho

O par real foi recebido pelo Captador, e a barreira prova + gabarito funcionou. Foi tecnicamente possível obter texto estruturado e associar respostas neste experimento. Isso demonstra viabilidade para este caderno, não um pipeline universal ou uma extração certificada.

Para repetir o processo dentro do produto ainda faltam: descoberta/download de URLs no Captador, um Digitalizador com contrato, dependências e testes próprios, tratamento dos recursos visuais e a incorporação das questões pelo Organizador. O diagnóstico externo não deve ser confundido com uma funcionalidade implementada do repositório. Um futuro extrator deverá testar outros layouts e cadernos, preservar procedência/páginas e informar pendências.
