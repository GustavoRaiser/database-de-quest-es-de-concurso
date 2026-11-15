# Estado e evolução do Captador

Implementados: criação de lotes por prova/edição/caderno, upload de arquivos, leitura manual de pasta de entrada, associação de gabaritos preliminares/definitivos e retificações, preservação por SHA-256, integridade, pendências e integração na interface do Emissor.

Entrega atual: lote de documentos originais pronto para ser consumido pelo Digitalizador, ainda sem questões extraídas. O gabarito pode chegar posteriormente ao mesmo lote. A prévia é documental e exibe limitações de processamento explicitamente.

Próximas etapas: implementar o Digitalizador e seu contrato intermediário, ligar a extração à interface compartilhada e, depois, a incorporação pelo Organizador. Download por URL, adaptadores de API, acompanhamento automático de pasta e mapeamento de respostas extraídas ainda estão planejados. A desatualização jurídica continua sendo informação manual do usuário.

Implementados no contrato v2: protocolos órgão.cargo.prova, filtros de registro inspirados nos filtros públicos de provas do Qconcursos, histórico documental, identificação de lotes antigos e fila de encaminhamentos. A fila só recebe prova e gabarito íntegros vinculados. A análise pode ser registrada manualmente com relatório, sem execução automática do Digitalizador.

Implementados agora: download HTTPS de PDF, descoberta de links em listagem HTML, entrega validada ao Digitalizador e registro distinto de extração programática. Os itens anteriores que tratavam essas funções como futuras são históricos; OCR, API externa e monitoramento de pasta permanecem pendentes.
