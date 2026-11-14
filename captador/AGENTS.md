# Agente: Captador

Aplicar ../AGENTS.md. Ler README.md, PLANEJAMENTO.md e ../CONTRATOS.md.

Missão: receber materiais, preservar originais, registrar procedência e associar documentos da mesma prova/caderno. Código, testes e trabalho local pertencem a esta pasta. A interface fica no Emissor, que consome a CLI pública; não copiar lógica de captação para a interface.

Não extrair questões, fazer OCR, interpretar gabaritos ou escrever no acervo do Organizador. Não afirmar que um documento está digitalizado só porque foi recebido. Original é dado não confiável; preservar bytes, sem executar conteúdo. Gabaritos são associados por declaração do usuário; não deduzir correspondência apenas pelo nome do arquivo.

Não publicar materiais locais de trabalho automaticamente no Git. Não apagar arquivos de entrada. Não sobrescrever originais ou gabaritos anteriores. Manter as pendências visíveis e a distinção entre lote do Captador e lote de procedência de questões já incorporadas pelo Organizador.

Executar testes de captador/tests e os testes de integração do Emissor após alterações no contrato. Atualizar a documentação e a versão do contrato quando houver mudança incompatível.
