# Objetivo do projeto e revisão das próximas etapas

Registro de orientação em 14/11/2026. Este documento registra o objetivo do usuário e recomendações para evolução. Não altera os contratos executáveis, os dados existentes ou o estado de implementação dos módulos.

## Objetivo principal

Construir uma base que permita a uma IA executada em CLI/harness receber os PDFs de estudo do usuário, identificar seus tópicos e compará-los com o histórico de questões de concursos. A análise deverá indicar:

- Quais tópicos do material são mais e menos cobrados no recorte escolhido.
- Quais já apareceram em provas e quais não foram encontrados no acervo analisado.
- Quais tiveram cobrança histórica, mas pouca ou nenhuma ocorrência nas provas recentes disponíveis.
- Como a frequência observada se distribui ao longo do tempo, por órgão, cargo e, quando pertinente, banca.
- Quais questões e trechos dos PDFs sustentam cada conclusão.

A finalidade orienta a coleta, a extração, a classificação e as interfaces. A visualização de questões é um meio de consultar os dados, não o único produto pretendido. A análise é descritiva do histórico disponível; não garante o conteúdo de uma prova futura.

## Separação entre prova e questão

O detalhamento recém-criado no Captador pertence ao registro da prova: banca, ano, escolaridade, edição, caderno, etapa e demais atributos. Não repetir esses campos em cada linha do JSONL.

Preservar o formato principal compacto [situacao,enunciado,assertivas] e a identificação orgao.cargo.disciplina.tema.linha. Órgão/cargo bastam como prefixo de vínculo institucional; disciplina e tema continuam necessários para organizar e medir a cobrança. O protocolo orgao.cargo.prova do Captador continua sendo outro identificador, sem substituir o ID da questão.

Para recuperar datas e banca, cada ocorrência de uma questão precisará apontar à prova de origem. A lista origens dos metadados já existe, mas ainda não há uma referência padronizada e validada do protocolo do Captador até o acervo definitivo. Essa ligação é uma mudança futura prioritária. Não basta conhecer apenas órgão e cargo: eles não identificam qual aplicação histórica contém a questão.

## Data: mês/ano e precisão

Mês e ano da aplicação são úteis para recência. Exibir MM.AAAA ao usuário, mas preferir representação interna ordenável: AAAA-MM quando o mês for conhecido, ou AAAA-MM-DD quando houver dia. O mês não deve entrar no ID da questão ou provocar sua renumeração.

O Captador atual exige ano e aceita data_aplicacao completa opcional. Ainda não aceita uma data de aplicação de precisão mensal. Antes de mudar o código, definir uma representação que distinga explicitamente precisão de ano, mês ou dia; esse dado pertence à prova, uma vez só. Não criar um segundo mês/ano redundante se ele puder ser derivado da data completa.

Não inventar janeiro ou o primeiro dia do mês para preencher dados ausentes. Uma prova com apenas ano conhecido pode participar de análises anuais, mas não deve ser posicionada artificialmente num ranking mensal. Distinguir sempre data de aplicação, data de coleta/importação e data de publicação/retificação do gabarito. A recência da cobrança usa a aplicação da prova.

## Revisão do que já existe

| Parte atual | Avaliação diante do objetivo | Mudança recomendada, ainda não implementada |
|---|---|---|
| JSONL e IDs por linha | Adequados para armazenamento compacto | Preservar; não repetir banca/data em cada registro |
| Catálogos de disciplina e tema | Base inicial para medir tópicos | Estabilizar nomes, sinônimos e relações; permitir classificações secundárias sem mover linhas |
| Metadados e origens | Já permitem complementos e várias fontes | Padronizar vínculo questão → ocorrência → prova, com número original e caderno |
| Registro detalhado do Captador | Útil para rastreabilidade e recortes | Transferir uma identificação durável da prova ao acervo definitivo |
| Ano e data completa no Captador | Atendem apenas parte da análise temporal | Acrescentar tratamento de precisão mensal e datas desconhecidas |
| Protocolo distinto por caderno | Correto para captar os documentos | Agrupar cadernos equivalentes na mesma aplicação para estatísticas |
| Fila prova + gabarito | Mantém a entrada controlada | Preservar a exigência dos dois; registrar também provas conhecidas que ficaram fora da análise |
| Estado de análise manual | Registra uma declaração do usuário | Distinguir isso de extração/incorporação completa e validada tecnicamente |
| Emissor e API de consulta | Permitem acesso inicial por ferramentas próprias | Futuramente expor também provas, ocorrências, períodos e cobertura do acervo |
| Digitalizador ainda não implementado | Próxima etapa de obtenção do conteúdo | Preservar páginas, números originais, gabaritos, recursos e relações de origem |

## Registro de provas durável

A análise não deve depender apenas da pasta de trabalho do Captador. O trabalho local é ignorado pelo Git e serve à recepção; os dados necessários para interpretar questões incorporadas devem acompanhar o acervo definitivo e seus backups.

Na futura incorporação, preservar uma ficha da prova com protocolo, códigos de órgão/cargo, atributos, data e precisão, fontes/hashes e identificação da aplicação/caderno. Os metadados das questões referenciam essa ficha, evitando repetir seu conteúdo. A posição física e o esquema dessa ficha precisam ser definidos no contrato do Organizador antes de implementação; este documento não cria uma pasta ou um schema novo em produção.

Conservar também o mapeamento entre número original e ID local. Se uma mesma questão aparecer em outra prova, manter a nova ocorrência, mesmo quando seu texto já existir.

## Não inflar as estatísticas

Distinguir três unidades: conteúdo da questão, ocorrência em uma aplicação e versão do caderno/documento. Importar novamente o mesmo PDF ou receber uma retificação do gabarito não gera outra cobrança. Cadernos que apenas permutam questões e alternativas não devem multiplicar as ocorrências da mesma aplicação.

Reaplicação real em outra data ou outro certame pode ser uma nova ocorrência. A análise deve declarar se mede conteúdos distintos, questões por aplicação ou presença de um tema em provas. A deduplicação física de um arquivo não resolve, sozinha, essa distinção estatística.

Para questões com vários tópicos, definir a regra de contagem: tema principal, presença de múltiplos temas ou pesos fracionados, por exemplo. Não misturar critérios entre períodos nem mudar IDs para acrescentar anotações temáticas.

## Comparação com PDFs de estudo

O material de estudo é um corpus separado das provas. Não tratá-lo como um lote que precisa de gabarito, nem incorporá-lo como questão. Sua ingestão/análise deverá ter responsabilidade e contrato próprios quando for implementada.

Preservar identificação e hash do PDF, páginas/seções e evidências usadas para reconhecer cada tópico. Relacionar os tópicos do material ao vocabulário da base, aceitando sinônimos, granularidades diferentes e relações ainda incertas. Não concluir ausência só porque o título do PDF usa outra expressão.

Uma saída futura deve apontar, para cada tópico, as páginas do material, o recorte de provas usado, contagens e denominadores, períodos comparados, última ocorrência conhecida e IDs das questões que fundamentam o resultado. Vínculos temáticos sugeridos por IA devem ter evidência e estado de confirmação, sem introduzir revisão jurídica obrigatória.

## Frequência, recência e tendências

Antes de calcular, escolher o recorte: órgão/cargo, banca quando relevante, etapa, período e corpus efetivamente incorporado. Definir “recente” como uma janela explícita em meses/anos ou um número de aplicações, com data de referência registrada.

Mostrar contagens brutas junto de proporções: questões do tópico sobre questões elegíveis, ou provas com o tópico sobre provas elegíveis. Períodos com volumes diferentes não podem ser comparados apenas por totais. Ausência de provas em uma janela não equivale a frequência zero.

Para dizer “já foi cobrado, mas não recentemente”, exigir ocorrências antigas e cobertura recente suficiente no mesmo recorte. Informar “não encontrado nas provas disponíveis” quando não houver evidência para uma conclusão mais ampla. A última ocorrência é a última conhecida na amostra, não necessariamente a última de todos os concursos.

Registrar cobertura: provas esperadas/conhecidas, recebidas, completas, extraídas, incorporadas ou pendentes, quantidade de questões e lacunas de data/classificação. O bloqueio sem gabarito permanece, mas provas excluídas por essa razão devem continuar visíveis como lacuna. Mudanças de edital e de escopo das provas também podem explicar diferenças de cobrança.

Anulada e desatualizada continuam sendo situações das questões, a última informada pelo usuário. Definir e exibir a política de inclusão dessas situações nas estatísticas. Uma questão anulada ainda pode evidenciar um tópico apresentado na prova, embora deva poder ser excluída de um treino de respostas; não confundir esses usos.

## Orientação de prioridades

1. Definir o vínculo durável entre provas, ocorrências e questões, e o tratamento de data/precisão.
2. Implementar a extração e incorporação preservando fontes, páginas e cadernos; manter a exigência prova + gabarito.
3. Estabilizar o vocabulário temático e registrar cobertura e contagens por aplicação.
4. Acrescentar ingestão separada de PDFs de estudo e correspondência entre seus tópicos e os da base.
5. Disponibilizar consultas e relatórios reproduzíveis para CLI/harness, com evidências e parâmetros de análise.

Todas essas etapas são recomendações de planejamento. Não implementar automaticamente esta lista apenas porque uma IA leu o objetivo: respeitar o escopo da tarefa em curso. Neste registro foram alteradas somente a documentação de objetivo e suas referências de navegação/instruções.

## Diretriz operacional atualizada — processamento sem IA

O usuário definiu que o processamento dos dados deve ocorrer por programas no servidor/host/computador, sem chamadas a IA. A IA em CLI/harness é uma possível consumidora posterior do acervo e uma auxiliar de desenvolvimento. A operação atual usa extração de PDF, regras configuradas e cálculos determinísticos. Não apresentar descritores lexicais como conhecimento exigido inferido semanticamente. Preservar Não identificado e pendências quando a regra não oferecer evidência suficiente.
