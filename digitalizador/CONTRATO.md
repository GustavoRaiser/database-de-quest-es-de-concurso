# Extração intermediária v1 — enam_fgv

Entrada: encaminhamento atual validado pela CLI entrega do Captador. Exige prova e gabarito PDF, caderno Tipo 1 e perfil de layout ENAM/FGV (duas colunas, 80 questões A–E). O programa confere o cabeçalho da prova; não pretende extrair qualquer PDF arbitrário.

Saída: objeto versao 1, extrator, encaminhamento, protocolo, identificacao, documentos, questoes, pendencias, estado e contagens. Cada questão usa numero_original, disciplina extraída de cabeçalho, enunciado, assertivas, rotulos_originais, paginas, gabarito, abordagem e pendencias. Não recebe ID local definitivo nem situação atualizada automaticamente.

O gabarito refere-se exclusivamente ao Tipo 1; * representa anulação se a legenda do documento confirmar. Posições das respostas começam em 1. Texto e originais são preservados; recursos visuais no corpo geram pendência com referência à página do original. O estado extraido_com_pendencias não libera incorporação automática.

Saídas ficam em digitalizador/trabalho/ID.json, excluídas do Git, com escrita atômica. A identidade depende do pacote e da implementação do extrator e dos descritores. Nova versão gera resultado separado. Cada execução verifica o pacote e os originais novamente. A extração é refeita; resultados idênticos têm o mesmo nome, sem criar cópias adicionais. Não registrar extração como análise manual do usuário no Captador.

Descritores são gerados pelo comando público descrever-candidatos do Organizador, por regras locais. Não usam modelo de IA e não comprovam equivalência semântica. Sem correspondência, o valor é Não identificado. O Compilador e a incorporação no acervo definitivo continuam fora deste contrato.
