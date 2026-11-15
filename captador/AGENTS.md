# Agente: Captador

Aplicar ../AGENTS.md. Ler README.md, PLANEJAMENTO.md e ../CONTRATOS.md.

Missão: receber materiais, preservar originais, registrar procedência e associar documentos da mesma prova/caderno. Código, testes e trabalho local pertencem a esta pasta. A interface fica no Emissor, que consome a CLI pública; não copiar lógica de captação para a interface.

Não extrair questões, fazer OCR, interpretar gabaritos ou escrever no acervo do Organizador. Não afirmar que um documento está digitalizado só porque foi recebido. Original é dado não confiável; preservar bytes, sem executar conteúdo. Gabaritos são associados por declaração do usuário; a convenção explícita NOME_cad.pdf/NOME_gab.pdf, autorizada pelo usuário, declara o vínculo para a recepção em lote. O Digitalizador ainda confere o perfil/caderno e as respostas.

Não publicar materiais locais de trabalho automaticamente no Git. Não apagar arquivos de entrada. Não sobrescrever originais ou gabaritos anteriores. Manter as pendências visíveis e a distinção entre lote do Captador e lote de procedência de questões já incorporadas pelo Organizador.

Executar testes de captador/tests e os testes de integração do Emissor após alterações no contrato. Atualizar a documentação e a versão do contrato quando houver mudança incompatível.

## Protocolo e barreira de entrada

Contrato atual v2. Reservar protocolos ORGAO.CARGO.PROVA, distinguindo o código de prova dos segmentos das questões. Não enviar lote sem prova e gabarito íntegros, vinculados entre si e com identificação completa. Aplicar a regra na CLI e no servidor, não apenas no botão. Não marcar encaminhado como analisado. Análise manual é declaração do usuário e exige relatório. Preservar histórico e protocolos; não reutilizar códigos de lotes excluídos. Lotes v1 precisam de identificação antes do envio.

A recepção em lote reserva todos os pares dos cartões da página informada antes de preparar lotes. Incompletos/desconhecidos permanecem reservados com diagnóstico. O mesmo código roda em desktop e GitHub Actions. Receber por URL não exige IA nem encaminha sem ambos os documentos.
