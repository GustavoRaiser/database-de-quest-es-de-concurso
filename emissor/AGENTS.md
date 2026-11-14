# Agente: Emissor

Aplicar ../AGENTS.md. Ler README.md e PLANEJAMENTO.md. Responsabilidade: apresentar e disponibilizar questões para leitura, com filtros opcionais e metadados completos.

Manter servidor, interface, testes e instruções nesta pasta. Usar a CLI pública do Organizador para consultas; não importar seu código interno nem duplicar o acervo. Recursos locais seguem o contrato de hash documentado. Não escrever na base. Nunca interpretar HTML de questões como código da interface. Não expor o servidor local em rede sem definir autenticação e operação adequadas.

Sem filtros significa toda a base, com paginação; não limitar silenciosamente ao primeiro tema ou órgão. Filtros usam chaves completas sensíveis a maiúsculas/minúsculas. Preservar identidade por linha, textos de apoio, ordem e posição de recursos. Atualização jurídica e revisão de conteúdo não pertencem a este módulo; a situação é exibida como cadastrada.

Verificação: executar `python -m unittest discover -s emissor/tests -v` na raiz. Mudanças no contrato público também precisam manter os testes do Organizador passando.
