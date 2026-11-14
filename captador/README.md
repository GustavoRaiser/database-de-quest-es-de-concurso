# Captador

Recebe e preserva documentos antes da digitalização. Implementado em Python 3.10+, sem dependências externas. Entradas atuais: envio de arquivo e seleção de arquivo de uma pasta local. URLs podem ser registradas como procedência; download por URL e adaptadores de API ficam para uma etapa posterior.

## Usar na interface compartilhada

Na raiz do repositório:

```sh
python emissor/servidor.py --base organizador/exemplos/base
```

Abra http://127.0.0.1:8000 e escolha **Adicionar material**.

1. Crie um lote identificando prova, edição e caderno. Cargo e fonte são opcionais.
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

## Contrato do lote — versão 1

`lote.json` contém versao, id, criado_em, identificacao e documentos. Identificação inclui prova, edicao, caderno, cargo e fonte. Cada documento registra nome_original, arquivo, sha256, tamanho, tipo, situacao_gabarito, referente_a, recebido_em, canal e url_origem.

- Tipos: prova, gabarito, retificacao, complemento.
- Gabarito: preliminar ou definitivo. “Anulada” é informação de uma questão, não o estado de todo o documento de gabarito.
- referente_a: SHA-256 da prova do lote, para gabarito e retificação.
- Caminhos de originais são relativos à pasta do lote. Arquivos são nomeados pelo hash sem extensão; o nome original é preservado no manifesto.
- Mesmo hash no mesmo lote é recusado. O mesmo nome com conteúdo diferente pode ser recebido como outro documento.
- Leitura verifica existência e hash dos originais; problemas são apresentados na listagem de lotes.
- Gravações são serializadas por .captador.lock e o manifesto é substituído atomicamente. Em caso de interrupção, conferir o lote antes de remover um bloqueio restante ou arquivos não referenciados.

A consulta calcula estado e pendências: aguardando_prova ou pronto_para_digitalizador. A ausência de gabarito é informada como pendência, mas permite preparar a extração da prova. `processamento: nao_iniciado` é explícito: estar pronto não significa que houve digitalização.

## Interface pública por CLI

Na raiz:

```sh
python captador/app.py estado
python captador/app.py --raiz /caminho/trabalho estado
```

`criar` e `anexar` recebem um objeto JSON pela entrada padrão e retornam JSON. `criar` exige prova, edicao e caderno. `anexar` exige lote, nome, tipo e conteudo_base64 para upload, ou entrada igual a nome para copiar um arquivo da pasta de entrada. Para gabarito, exige situacao_gabarito. url_origem é opcional. Exemplos completos estão nos testes.

O Emissor utiliza essa CLI, sem importar código interno. Endpoints da interface: GET /api/captacao; POST /api/captacao/criar e /api/captacao/anexar. POST exige application/json, Origin correspondente ao servidor e X-Captacao-Token obtido na consulta de estado. O limite HTTP é 22 MiB para acomodar um arquivo de 15 MiB codificado em base64. O servidor continua restrito a localhost.

## Entrega e limites

Os lotes são a entrada futura do Digitalizador. Nesta etapa, a prévia mostra documentos, hashes, vínculos, estado e pendências; não mostra questões extraídas. Extração de PDF/OCR, interpretação do gabarito e incorporação ao acervo ainda não foram implementadas. A interface informa isso e não oferece um botão de extração sem processamento real.

Depois da digitalização, o número original e o caderno permitirão associar a resposta à questão. No formato definitivo, o gabarito fica na chave da questão em TEMA_md.json: por exemplo, `"12": {"gabarito": {"situacao":"definitivo","alternativas_corretas":[3],"rotulos_originais":["C"]}}`, além dos demais campos obrigatórios. A posição 3 significa terceira assertiva local, contada a partir de 1. Nenhuma resposta é inferida pelo Captador.

## Testar

```sh
python -m unittest discover -s captador/tests -v
python -m unittest discover -s emissor/tests -v
```
