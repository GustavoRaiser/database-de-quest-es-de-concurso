# Estado e próximos passos

Implementado: CLI própria; leitura do snapshot público do Organizador; cálculo lexical com quatro dimensões/pesos e cobertura; aproveitamento de perfis/conceitos; índice invertido e modo exaustivo; comparação de pares e busca por ID; grupos conservadores sem transitividade; arquivos derivados versionados por hash; vínculo a ocorrências/provas; integração após incorporação no pipeline desktop/GitHub; testes.

Pendente: calibrar pesos/cortes com pares representativos declarados pelo usuário; melhorar vocabulários e sinônimos sem transformar ocorrências lexicais em compreensão semântica; comparar resultados de busca com amostra exaustiva para medir perda de recuperação; exibir grupos no Emissor. Não implementar essas etapas apenas por ler este plano.

Frequência/recência e comparação com PDFs de estudo são necessidades posteriores, que dependem de cobertura, datas, unidades de contagem e deduplicação de aplicações/cadernos. Grupos atuais não resolvem isso automaticamente. O usuário autorizou modelos locais exclusivamente no Compilador; o modo lexical permanece independente.

## Modo semântico adicional

Implementado o modo conjunto lexical + IA local no Compilador, com saídas separadas, registro de execução, identificação de modelos, evidências e cache. A autorização de IA limita-se ao Compilador; os demais módulos seguem por código convencional. Ver [SEMANTICA.md](SEMANTICA.md). O serviço Ollama e modelos precisam estar instalados no ambiente executor; a avaliação real dos modelos e a preparação de runner semântico permanecem pendentes.

## Prioridade semântica pelo harness

O modo semântico padrão prepara tarefas para a IA do harness, com comandos de registro e consolidação, hashes de entrada, autoria/modelo declarados, retomada e histórico de respostas. Ver [HARNESS.md](HARNESS.md). O pipeline prepara essas tarefas após a análise lexical, sem invocar IA. A conclusão documental e a conclusão das respostas semânticas são estados distintos no relatório. IA local exige seleção explícita e --habilitar-ia-local, sem fallback automático.
