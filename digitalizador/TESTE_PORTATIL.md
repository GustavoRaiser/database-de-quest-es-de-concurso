# Verificação da cadeia portátil — 15/11/2026

Execução real a partir da URL fornecida pelo usuário:

`https://www.qconcursos.com/questoes-de-concursos/provas?by_institute%5B%5D=10726`

O Captador descobriu seis cartões e reservou seis cadernos e seis gabaritos, sem chamadas a modelos. O ENAM 2026.1 foi encaminhado e extraído: 80 questões, 400 alternativas, uma anulação reconhecida. O Organizador incorporou as 80 questões em oito disciplinas, cada uma com tema Não classificado, com metadados/gabaritos, ficha da prova e mapeamento. Preservou os dois PDFs e 30 PNGs integrais das páginas que contêm elementos visuais/vetoriais (inclui elementos de diagramação, sem afirmar que todas têm figuras de questões).

As outras cinco reservas não foram marcadas como incorporadas: três exigem declaração da condição do gabarito e duas também têm identificação incompleta pelo título. Nenhum par recebido foi descartado. O relatório geral retornou código 2, indicando processamento parcial, com motivos por item.

Outra execução com as duas URLs diretas do ENAM 2026.1 reconheceu o par pelos caminhos do Qconcursos, reaproveitou os arquivos reservados e retornou ja_incorporado, novas_questoes 0. A base de teste manteve 80 questões. Os arquivos reais ficaram somente nas pastas de trabalho ignoradas pelo Git; o acervo principal versionado permanece vazio e os exemplos continuam fictícios.

O adaptador executar_github.py também foi executado localmente, com as mesmas variáveis de entrada do workflow, usando PDFs sintéticos: completou a cadeia e produziu a estrutura de artefato prevista. O YAML foi validado. **Isso não equivale a uma execução no runner do GitHub**; a primeira execução remota deve ser iniciada em Actions, pelo workflow publicado.

Verificações automatizadas: 79 testes aprovados (Captador 23, Organizador 38, Digitalizador/pipeline 7, Emissor 11). Cobrem par incompleto, downloads parciais, associação de URLs, falhas de layout/gabarito, incorporação, repetição sem duplicatas, acréscimos preservando linhas, recusa de outro gabarito para prova incorporada, gravação interrompida e recuperação. Também foram validadas a base vazia, a base fictícia e a base real de teste.

Limites mantidos: apenas perfil ENAM/FGV Tipo 1 textual; não faz OCR, classificação semântica, reconstrução de figuras dentro de alternativas, agrupamento ou atualização jurídica automática. Dados de trabalho e artefatos exigem backup; retenção do artefato configurada em 30 dias.
