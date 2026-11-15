# Captador

Recebe e preserva documentos antes da digitalização. Implementado em Python 3.10+, sem dependências externas. Entradas atuais: envio de arquivo e seleção de arquivo de uma pasta local. URLs diretas de PDF podem ser baixadas pelo Captador. Também há descoberta de pares em cartões de listagem HTML (testada no Qconcursos). Adaptadores de API continuam futuros.

## Usar na interface compartilhada

Na raiz do repositório:

```sh
python emissor/servidor.py --base organizador/exemplos/base
```

Abra http://127.0.0.1:8000 e escolha **Adicionar material**.

1. Registre a prova com órgão/cargo (códigos e nomes), banca, ano, prova, edição e caderno. Escolaridade, áreas de atuação/formação, UF, esfera, etapa, data de aplicação, edital e fonte complementam a identificação.
2. Selecione o lote e envie primeiro o documento de questões como prova.
3. Envie o gabarito do mesmo caderno, informando preliminar ou definitivo.
4. Acrescente retificações e complementos, quando houver. O gabarito também pode chegar depois.

A associação com a prova é declarada pelo usuário ao selecionar o lote. A ferramenta não lê os PDFs para confirmar edição/caderno. Um lote aceita uma prova; outro caderno ou outra prova exige outro lote. Vários gabaritos e retificações são preservados como documentos separados, com data e vínculo ao hash da prova; nenhum substitui outro silenciosamente.

## Entrada por pasta

Na primeira abertura da área de captação, a ferramenta cria:

```text
captador/trabalho/
    entrada/
    recebidos/
        ID-DO-LOTE/
            lote.json
            originais/
                SHA256-COMPLETO
```

Coloque arquivos diretamente em entrada/ (sem subpastas). Na interface, clique **Verificar pasta e atualizar lotes**, selecione a origem “Arquivo da pasta de entrada”, escolha o arquivo e receba-o no lote. Esse processo copia os bytes sem mover ou apagar o arquivo de entrada. Não há monitoramento automático.

Use `--captacoes /caminho/de/trabalho` ao iniciar o Emissor para mudar a pasta. Os diretórios entrada/ e recebidos/ serão criados dentro dela. Arquivos locais em captador/trabalho/ são ignorados pelo Git; inclua essa pasta no seu backup. O acervo definitivo do Organizador permanece separado.

Aceitos: PDF, PNG, JPEG, GIF, JSON, JSONL, HTML e TXT; até 15 MiB por arquivo. A extensão permite receber o documento, mas não garante que seu conteúdo seja válido. O Captador preserva bytes sem executar ou interpretar o material. Links simbólicos de entrada são recusados.

## Contrato do lote — versão 2

`lote.json` contém versao, id físico, grupo, protocolo, criado_em, identificacao, documentos e historico. O registro completo é o próprio manifesto do lote; não há um arquivo central gigante. Cada documento registra nome_original, arquivo, sha256, tamanho, tipo, situacao_gabarito, referente_a, recebido_em, canal e url_origem.

- Tipos: prova, gabarito, retificacao, complemento.
- Gabarito: preliminar ou definitivo. “Anulada” é informação de uma questão, não o estado de todo o documento de gabarito.
- referente_a: SHA-256 da prova do lote, para gabarito e retificação.
- Caminhos de originais são relativos à pasta do lote. Arquivos são nomeados pelo hash sem extensão; o nome original é preservado no manifesto.
- Mesmo hash no mesmo lote é recusado. O mesmo nome com conteúdo diferente pode ser recebido como outro documento.
- Leitura verifica existência e hash dos originais; problemas são apresentados na listagem de lotes.
- Gravações são serializadas por .captador.lock e o manifesto é substituído atomicamente. Em caso de interrupção, conferir o lote antes de remover um bloqueio restante ou arquivos não referenciados.

A consulta calcula estado e pendências: aguardando_prova, aguardando_gabarito, aguardando_identificacao ou pronto_para_digitalizador. Só é liberado o lote identificado que contenha uma prova e ao menos um gabarito íntegro vinculado ao hash dessa prova. Sem ambos, não há encaminhamento, mesmo por chamada direta à CLI ou API. Estar pronto não significa que houve digitalização.

## Interface pública por CLI

Na raiz:

```sh
python captador/app.py estado
python captador/app.py --raiz /caminho/trabalho estado
```

`criar` e `anexar` recebem um objeto JSON pela entrada padrão e retornam JSON. `criar` exige os campos descritos na identificação v2 (strings). `anexar` exige lote, nome, tipo e conteudo_base64 para upload, ou entrada igual a nome para copiar um arquivo da pasta de entrada. Para gabarito, exige situacao_gabarito. url_origem é opcional. Exemplos completos estão nos testes.

O Emissor utiliza essa CLI, sem importar código interno. Endpoints da interface: GET /api/captacao; POST /api/captacao/criar, /anexar, /identificar, /encaminhar e /registrar_analise (sob /api/captacao). POST exige application/json, Origin correspondente ao servidor e X-Captacao-Token obtido na consulta de estado. O limite HTTP é 22 MiB para acomodar um arquivo de 15 MiB codificado em base64. O servidor continua restrito a localhost.

## Entrega e limites

Os lotes são a entrada do Digitalizador. A área de captação mostra documentos, hashes e vínculos; após processamento, a interface apresenta a prévia das questões extraídas. A extração ENAM/FGV Tipo 1 e a leitura do gabarito são executadas pelo Digitalizador. OCR permanece futuro; a incorporação já é feita pelo Organizador no pipeline CLI. A interface oferece processamento real do perfil suportado e apresenta suas pendências.

Depois da digitalização, o número original e o caderno permitirão associar a resposta à questão. No formato definitivo, o gabarito fica na chave da questão em TEMA_md.json: por exemplo, `"12": {"gabarito": {"situacao":"definitivo","alternativas_corretas":[3],"rotulos_originais":["C"]}}`, além dos demais campos obrigatórios. A posição 3 significa terceira assertiva local, contada a partir de 1. Nenhuma resposta é inferida pelo Captador.

## Testar

```sh
python -m unittest discover -s captador/tests -v
python -m unittest discover -s emissor/tests -v
```

## Protocolo e registro de provas

O grupo usa os mesmos dois primeiros códigos das questões: `ORGAO.CARGO`. Cada prova/caderno recebe um terceiro código sequencial em base 62, próprio do Captador: `N32.a2.0`, `N32.a2.1`, … O terceiro segmento não é disciplina e não é a linha da questão. O UUID continua sendo o endereço físico do lote, preservando compatibilidade com os arquivos já recebidos.

O código do cargo é local ao órgão: informar `a2`, não `N32.a2`, no campo cargo_id. Valores diferenciam maiúsculas/minúsculas. Códigos conhecidos são sugeridos pelo catálogo do Organizador, e nomes conflitantes são recusados. Novos códigos podem ser reservados no Captador com seus nomes; não são cadastrados automaticamente no Organizador. Antes da incorporação, os catálogos devem ser compatibilizados. O Captador recusa nomes conflitantes entre seus próprios registros.

Protocolo é estável: documentos adicionais, gabaritos e análises não o alteram. Não excluir lotes nem reutilizar protocolos. O próximo código é obtido sob bloqueio a partir dos registros existentes. Mesma combinação de órgão/cargo, prova, banca, ano, edição, caderno e etapa é recusada como duplicata; o erro informa o protocolo para retomar. Comparações textuais ignoram caixa e espaços extras, mas os IDs preservam a distinção de caixa.

A área Registro de provas permite filtros por órgão, cargo, banca, ano, escolaridade, área de atuação/formação, UF, esfera, etapa, documentação e processamento, além de palavra-chave. São filtros combináveis sobre os registros locais. Ano é o ano de aplicação, informado em quatro dígitos; data de aplicação usa AAAA-MM-DD.

Referência consultada em 14/11/2026: [filtros públicos de provas do Qconcursos](https://www.qconcursos.com/questoes-de-concursos/provas). Instituição, banca, ano, cargo, escolaridade e áreas de atuação/formação vêm dessa referência. Caderno, edição, etapa, edital, localização, protocolo e estados são complementos do nosso projeto. Não houve importação de questões ou de listas de categorias do site.

## Encaminhar com segurança

Escolha explicitamente um gabarito do lote e clique **Encaminhar prova + gabarito**. Preliminar ou definitivo são aceitos; a escolha é preservada, sem presumir qual arquivo é o correto. A correspondência semântica de edição/caderno ainda depende da declaração do usuário, pois o PDF não foi interpretado.

Na CLI, `encaminhar` recebe `{"lote":"UUID","gabarito_sha256":"HASH"}` via entrada padrão. A operação valida novamente identificação, integridade de todos os arquivos, unicidade da prova e vínculo do gabarito. Retificações/complementos acompanham o pacote.

O pacote versionado é salvo em `encaminhamentos/HASH.json`, dentro da pasta de trabalho. Sua identidade deriva da identificação e dos documentos selecionados; repetir a mesma entrega não duplica o arquivo nem o evento no histórico. O pacote contém o protocolo, lote, identificação e descritores da prova/gabarito/complementos, com raiz_originais relativa à pasta de trabalho. O manifesto registra o encaminhamento e um evento datado.

A fila pertence ao Captador; o Digitalizador deve consumir o contrato público, conferir a integridade e o encaminhamento atual do lote antes de processá-lo. Criar um pacote não executa o Digitalizador. A recepção de novo documento invalida o encaminhamento atual e a análise atual; os eventos e pacotes antigos permanecem históricos e exigem novo encaminhamento para a versão atual.

## Registro de análise e migração

Histórico registra cadastro, documentos recebidos, encaminhamentos e análises declaradas. A interface permite registrar manualmente conclusão ou falha com um relatório, após encaminhamento válido. Isso registra uma declaração do usuário; não produz questões extraídas nem altera sua atualidade jurídica.

A CLI `registrar_analise` exige lote, encaminhamento atual, resultado (concluida/falha) e relatorio. A resposta exibe a análise atual e o histórico preserva as anteriores. O processamento não é rotulado automaticamente como concluído ao receber arquivos.

Lotes v1 continuam legíveis e seus originais não são alterados, mas ficam bloqueados para envio. Use **Identificar lote antigo**, preencha os novos campos e salve; o comando `identificar` também aceita a identidade completa mais lote via entrada padrão. Ele reserva o protocolo e grava a versão 2, preservando UUID, arquivos e documentos. A versão do acervo do Organizador permanece 3; esta é apenas a evolução do contrato de captação.

## URL e entrega para processamento local

Na interface, use Buscar links de prova e gabarito para uma página HTML ou Baixar PDF por URL para um endereço direto. A descoberta não cria lotes nem presume identidade: selecione os documentos e registre os atributos da prova. Outros layouts de páginas podem não ser reconhecidos. Arquivo vazio, HTML no lugar de PDF ou resposta HTTP de erro não são recebidos como prova.

A CLI descobrir recebe {"url":"https://…"}. anexar também aceita url em vez de entrada/conteudo_base64, mantendo nome, tipo e lote. O download aceita apenas HTTPS público, sem credenciais no endereço, limita tamanho e redirecionamentos e verifica cada destino. Respeita proxy HTTP confiável configurado no sistema para túnel HTTPS; credenciais do proxy não são registradas. Origem e URL final ficam no descritor. Download não interpreta o conteúdo como instrução.

A operação pública entrega retorna apenas um pacote atual, completo e íntegro. registrar_extracao registra o resultado programático no histórico e no estado do lote; não equivale a registrar_analise manual. Novos documentos invalidam o encaminhamento e a extração atuais. Essas operações são usadas pelo Digitalizador, e não expostas como edição arbitrária da base definitiva.

## Receber URLs/pasta em lote

A [operação portátil](../digitalizador/OPERACAO.md) usa os comandos `receber` e `preparar-reserva`. O primeiro reserva todos os pares da página Qconcursos ou da pasta, sem extrair conteúdo; o segundo prepara um lote completo, identificado e vinculado para encaminhamento. A convenção `NOME_cad.pdf` / `NOME_gab.pdf` declara o vínculo. `estado` inclui também reservas, além dos lotes.

Reservas ficam em `reservados/ID/registro.json`, `conteudo_cad.pdf` e `conteudo_gab.pdf`, dentro da raiz configurada. Não apagam as entradas. Falhas de download são registradas e podem ser retomadas. URLs já reservadas preservam seus bytes; para novas versões de um arquivo no mesmo endereço usar recepção explícita, sem sobrescrever a reserva anterior. Cada página informada tem seus próprios cartões; não há paginação implícita. Para dois PDFs diretos genéricos, usar prova_url/gabarito_url no pedido; pares de URLs `_cad/_gab` e caminhos arquivo_prova/arquivo_gabarito do Qconcursos são reconhecidos.

No workflow, o Captador roda no runner e suas pastas acompanham o artefato `acervo-processado`. No desktop, tudo fica local. Hash previamente conferido pode identificar condição do gabarito; os demais exigem declaração preliminar/definitivo. Identidade ENAM inferida de título/nome é proposta: a capa será conferida pelo Digitalizador. Para nomes genéricos, informar identidade no pedido.
