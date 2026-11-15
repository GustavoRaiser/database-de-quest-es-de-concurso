# Emissor

Visualização local de questões e API JSON de leitura para ferramentas próprias. Python 3.10 ou superior, sem dependências externas.

## Executar

Na raiz do repositório, para visualizar a amostra fictícia:

```sh
python emissor/servidor.py --base organizador/exemplos/base
```

Abrir http://127.0.0.1:8000 no navegador. Para o acervo real (atualmente vazio):

```sh
python emissor/servidor.py --base organizador
```

É possível escolher outro diretório de base e outra porta com `--base CAMINHO --porta 8001`. Encerre com Ctrl+C. A aplicação executa localmente; publicar o código no GitHub não hospeda o servidor. O endereço fica restrito ao computador que executa o comando.

## Funcionamento

Órgão, cargo, disciplina e tema são filtros opcionais, combinados por interseção. Qualquer um pode ser usado sozinho. Sem filtros, todas as questões da base participam da consulta; a navegação usa páginas de 20, 50 ou 100 registros. Menos filtros ampliam ou mantêm o conjunto encontrado. Combinações incompatíveis apresentam zero resultados.

Os seletores mostram o caminho dos nomes, pois códigos e nomes de categorias podem se repetir sob pais diferentes. Selecionar um cargo não exige selecionar primeiro o órgão. Limpar filtros retorna à primeira página de toda a base.

A ferramenta exibe enunciado, alternativas em quantidade livre, situação registrada, textos de apoio e imagens PNG/JPEG/GIF associadas às posições documentadas. Gabarito e procedência ficam em detalhes expansíveis. SVG, HTML, PDF, originais e outros formatos são disponibilizados para download, sem executar conteúdo externo. Textos são inseridos como texto, preservando quebras, sem interpretar HTML. A interface não avalia atualidade jurídica nem modifica questões.

## Integração própria

- `GET /api/catalogos`: os quatro catálogos, com chaves completas.
- `GET /api/questoes`: itens, total, pagina, por_pagina e paginas.
- Parâmetros opcionais: `orgao`, `cargo`, `disciplina`, `tema`, `pagina` (a partir de 1) e `por_pagina` (1 a 100).
- Os valores dos filtros são chaves completas: `orgao=N32`, `cargo=N32.a2`, `disciplina=N32.a2.5`, `tema=N32.a2.5.y`.
- Cada item contém `id`, `questao` (array original), `metadados` (objeto ou null) e `classificacao` (nomes e IDs).
- `GET /recursos/XX/HASH`: recurso local com integridade verificada; formatos ativos são baixados como arquivo.
- Erros de parâmetros retornam HTTP 400 com `erro`; caminhos desconhecidos retornam 404. Não há endpoints de escrita no acervo definitivo nem CORS aberto. A recepção de documentos usa os endpoints específicos de captação.

Exemplo: http://127.0.0.1:8000/api/questoes?orgao=N32&pagina=1&por_pagina=20

Também é possível dispensar o servidor e consumir a CLI pública do Organizador:

```sh
cd organizador
python -m basequestoes --base exemplos/base catalogos
python -m basequestoes --base exemplos/base emitir --orgao N32 --por-pagina 20
```

O Emissor usa essa CLI como fronteira entre módulos, sem importar implementações internas. A validação completa acontece na inicialização do servidor. Consultas percorrem os arquivos selecionados para contar resultados; não existe índice de busca adicional nesta versão. Reinicie após mudanças estruturais da base e coordene gravações externas para não ler um lote incompleto.

## Testar

Na raiz:

```sh
python -m unittest discover -s emissor/tests -v
```

## Adicionar material

A interface agora inclui a área Adicionar material. Ela permite criar lotes, enviar arquivos, verificar a pasta de entrada e anexar gabaritos/retificações. O servidor delega essas ações ao Captador. Configure o armazenamento com --captacoes CAMINHO; padrão captador/trabalho/. Veja o [contrato do Captador](../captador/README.md). A captação ainda não extrai questões; a prévia mostra os documentos recebidos e suas pendências.

## Registro de provas e encaminhamento

Adicionar material agora exige os códigos e nomes de órgão/cargo, banca e ano, além de prova/edição/caderno. Campos opcionais permitem escolaridade, áreas, UF, esfera, etapa, edital e data. A lista de protocolos possui filtros próprios e histórico por prova. A interface sugere códigos conhecidos; novos códigos são referências do Captador, sem cadastrar categorias no Organizador.

O botão de encaminhar só é habilitado com prova e gabarito íntegros e identificação completa. O servidor e a CLI repetem a validação. O usuário escolhe o gabarito; a ação registra o pacote na fila e ainda não extrai PDFs. Lotes antigos têm ação de identificação. Há registro manual de resultado de análise, com relatório explícito do usuário.

## Download e processamento no host

Instale primeiro `python -m pip install -r digitalizador/requirements.txt`. Em Adicionar material, é possível buscar links em uma página e selecionar prova/gabarito ou informar uma URL direta. Após receber ambos, encaminhe e clique Processar ENAM Tipo 1 no computador. A API POST /api/digitalizacao/processar recebe {"lote":"UUID"}, usando a mesma proteção de origem e sessão da captação. A interface apresenta enunciados, alternativas, gabaritos, descritores locais, pendências e download do JSON intermediário.

A extração ocorre no servidor local, sem IA, com apenas um processamento simultâneo. Os resultados ficam em digitalizador/trabalho/ ou --digitalizacoes CAMINHO. Eles são separados do acervo definitivo. Outros layouts, OCR e incorporação automática não estão disponíveis. Descritores são lexicais e podem retornar Não identificado; não são uma compreensão semântica garantida.
