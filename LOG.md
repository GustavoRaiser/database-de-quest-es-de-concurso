# Registro de ações

Rastro cronológico (mais recente no fim) do que foi feito no projeto por IAs e colaboradores, para identificar o que mudou e por quê. Cada entrada: data, responsável, ação, arquivos tocados e resultado. Apenas registra; não altera contratos nem dados.

## 2026-11-15 — Avaliação geral dos módulos (somente leitura)

- Pedido: "avaliação geral dos objetos" (interpretado como os quatro módulos: organizador, captador, emissor, digitalizador).
- Ações: leitura de README, OBJETIVO, ARQUITETURA, CONTRATOS, READMEs dos módulos e AVALIACAO_PDF; execução de `basequestoes validar` na base de exemplo e dos testes unitários de organizador, captador e emissor.
- Arquivos alterados: apenas este LOG.md (criado). Nenhum código, dado ou contrato foi modificado.
- Resultado: validação da base de exemplo OK (1 tema, 4 questões, 1 metadado, 1 lote); testes OK — organizador 31, captador 15, emissor 10. Digitalizador sem código/testes (documentação apenas). Acervo real (organizador/manifesto.json) vazio.
- Achados: ver resposta da sessão (resumo abaixo).
  - Organizador, Captador e Emissor: implementados e coerentes com os contratos; Emissor usa a CLI pública do Organizador (sem importar código interno).
  - Digitalizador: lacuna principal — sem extrator e sem contrato intermediário versionado; bloqueia o fluxo PDF → questões.
  - Objetivo analítico (OBJETIVO.md): nenhum dos itens prioritários implementado (vínculo durável prova→ocorrência→questão, precisão de data, cobertura, ingestão de PDFs de estudo).
  - Documentação: README.md raiz não lista todos os arquivos atuais (OBJETIVO.md, ABORDAGEM.md, METADADOS.md, AVALIACAO_PDF.md, TESTE_ENAM_2026_1.md); não havia registro de ações até esta entrada.

## 2026-11-15 — Commit e push do registro (solicitado por hook de fim de sessão)

- Ação: commit de LOG.md na branch claude/avaliacao-objetos-w4t5ww e push para origin.
- Arquivos: LOG.md. Nenhum código, dado ou contrato alterado.

## 2026-11-15 — Segunda análise: leitura do código e experimentos (somente leitura)

- Pedido: "faça uma nova análise". Diferença em relação à primeira: leitura integral do código (organizador/basequestoes, captador/app.py, emissor/servidor.py) e experimentos em cópias temporárias fora do repositório.
- Arquivos alterados: apenas este LOG.md. Nenhum código, dado ou contrato modificado. Base real validada: 0 temas, 0 questões.
- Achados confirmados por execução:
  1. Organizador — custo quadrático: `Base.metadado` chama `Base.questao`, que relê o JSONL do início para cada chave de metadados. Num tema sintético, `validar` e `emitir` levaram 0,4 s com 500 questões e 5,2 s com 2.000 (4× questões → 14× tempo). `emitir` revalida todos os metadados do tema a cada página, e o Emissor corta o subprocesso em 120 s.
  2. Captador — protocolo reutilizado: após apagar a pasta do lote N32.a2.1, o lote seguinte recebeu de novo N32.a2.1 (`registrar_identidade` usa o menor número livre). captador/AGENTS.md proíbe reutilizar códigos de lotes excluídos.
  3. Captador — trava órfã: com `.captador.lock` remanescente, toda gravação falha com "[Errno 17] File exists", sem orientação (o Organizador orienta no caso equivalente).
  4. Captador — entrada JSON que não é objeto gera traceback (AttributeError não tratado em `main`); pela interface não ocorre.
- Achados por leitura (não executados):
  5. Desencontro Captador → Organizador: `Base.lote` exige URL em cada documento, data AAAA-MM-DD e ID `[a-z0-9_-]`; o Captador aceita URL vazia, grava data-hora ISO e emite protocolo com pontos e maiúsculas. Não há campo para o protocolo nas origens dos metadados.
  6. Captador — `ler` recalcula o SHA-256 de todos os originais a cada leitura; `criar` e `estado` percorrem todos os lotes.
  7. Captador — `identificar` substitui o histórico do lote v1 em vez de acrescentar.
  8. Emissor passa `catalogos.json` do Organizador por caminho ao Captador, em vez de usar o comando `catalogos` da CLI.
  9. Não há integração contínua: os 56 testes só rodam manualmente.
- Pontos sólidos verificados no código: gravação atômica com fsync, rejeição de chaves JSON duplicadas, contenção de caminhos, integridade por SHA-256, proteção de Host/Origin/token no POST do Emissor, recursos ativos servidos só como download.
