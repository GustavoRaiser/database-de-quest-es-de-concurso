# Teste integrado por programas — ENAM 2026.1

Executado em 15/11/2026 com a URL de listagem fornecida pelo usuário. Nenhuma chamada a modelo de IA foi feita no processamento.

## Percurso verificado

O servidor do Emissor foi iniciado em localhost, apontando para pastas de teste isoladas. As requisições HTTP foram dirigidas aos mesmos endpoints da interface:

1. Captador descobriu seis pares de links na página de provas filtrada por instituição 10726 do Qconcursos.
2. Foi registrado um lote ENAM/FGV 2026.1, Tipo 1, com protocolo de teste 0.0.0. Os códigos não foram reservados no acervo definitivo.
3. Captador baixou o PDF da prova pela URL descoberta, preservando bytes, origem e SHA-256.
4. Encaminhamento sem gabarito foi recusado com HTTP 400.
5. Captador baixou o gabarito selecionado e vinculou-o à prova; foi declarada a condição definitiva, já conferida contra a fonte oficial no teste anterior.
6. Lote completo foi encaminhado e o endpoint /api/digitalizacao/processar executou o Digitalizador.
7. O Organizador produziu descritores via seu comando público de regras locais. O resultado intermediário foi salvo pelo Digitalizador e o estado programático registrado no Captador.

## Resultado observado

| Verificação | Resultado |
|---|---:|
| Questões extraídas em sequência | 80 |
| Alternativas A–E | 400 |
| Respostas associadas | 80 |
| Questão anulada | 42 |
| Geração dos descritores | regras |
| Questões sem conceito no vocabulário inicial | 48 |
| Incorporação ao acervo definitivo | Não realizada |

O estado é extraido_com_pendencias. Foram indicados elementos visuais/vetoriais no corpo das páginas e a limitação lexical dos descritores. Os conceitos encontrados não foram tratados como interpretação jurídica ou equivalência semântica confirmada. Não se atribuiu situação atualizada às questões por inferência.

A extração foi feita pelas ferramentas versionadas do projeto, e não por um script externo de parsing como no diagnóstico anterior. A orquestração do teste apenas enviou as requisições HTTP. Os testes automatizados também percorrem recepção, fila e extração com PDFs sintéticos, incluindo recusa de documentos incompletos e pacotes obsoletos.

## Reprodução

Instalar as dependências e seguir digitalizador/README.md. O teste real usou arquivos em captador/trabalho/pipeline-sem-ia-enam20261/ e digitalizador/trabalho/pipeline-sem-ia-enam20261/, ambos ignorados pelo Git. PDFs, textos integrais e resultados das questões não foram publicados. A presente documentação registra apenas métricas e o funcionamento.

O suporte inicial permanece restrito ao perfil de layout ENAM/FGV Tipo 1 com texto. A prova completa não foi revisada visualmente questão a questão. OCR, outros cadernos/layouts, categorização temática confiável, similaridade e incorporação definitiva ainda são trabalhos posteriores.
