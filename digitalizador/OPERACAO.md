# Uma cadeia, dois ambientes

O programa executa no computador que o inicia. A IA/harness só entrega parâmetros e aciona a CLI. Download, extração, associação de respostas, descritores e gravação usam código, sem chamadas a modelos.

```text
URLs de páginas / par NOME_cad.pdf + NOME_gab.pdf
    ↓ Captador: descobrir links, baixar/copiar e reservar originais
    ↓ Captador: identificar lote, vincular o par e liberar entrega íntegra
    ↓ Digitalizador: extrair perfil suportado, respostas e páginas originais
    ↓ Organizador: validar, cadastrar hierarquia, anexar linhas e metadados
    ↓ Compilador: relações e grupos propostos por indícios lexicais
    ↓ Emissor / CLI / ferramentas próprias: consultar a base resultante
```

## Desktop e harness

Python 3.10+; instalar as dependências uma vez, enquanto houver conexão:

```sh
python -m pip install -r digitalizador/requirements.txt
python digitalizador/pipeline.py --url 'https://www.qconcursos.com/questoes-de-concursos/provas?by_institute%5B%5D=10726'
```

A URL é passada ao Captador. Ele reconhece os cartões de provas da página do Qconcursos e reserva **todos os pares encontrados naquela página**. Não percorre outras páginas automaticamente: informar as respectivas URLs, repetindo `--url`, quando necessário. Links com o mesmo endereço preservam a reserva existente; uma nova edição/retificação da mesma URL deve ser recebida explicitamente como nova versão, sem sobrescrever o arquivo antigo.

Para arquivos, inclusive totalmente offline:

```sh
python digitalizador/pipeline.py --pasta captador/entrada --situacao-gabarito definitivo
```

O sufixo é uma declaração de vínculo: `enam-2026.1_cad.pdf` e `enam-2026.1_gab.pdf`. Não é necessário montar um lote à mão. O prefixo ENAM/edição permite propor identificação; o Digitalizador confere a capa. Nomes genéricos precisam da identificação em `--pedido`. A opção definitivo acima é uma declaração de quem executa: usar apenas quando essa for a condição documentada da fonte. Sem os dois arquivos, o Captador reserva o que recebeu e não encaminha.

Opções de localização independentes do diretório atual:

- `--captacoes`: trabalho do Captador; padrão `captador/trabalho`.
- `--saida`: resultados e páginas do Digitalizador; padrão `digitalizador/trabalho`.
- `--base`: acervo do Organizador; padrão `organizador`.
- `--compilacoes`: trabalho do Compilador; padrão `compilador/trabalho`.
- `--relatorio`: resumo da execução; padrão `digitalizador/trabalho/pipeline.json`.

Para uma URL direta de prova, informar também a URL do gabarito no pedido. Exemplo de `pedido.json` (nomes e códigos de órgão/cargo podem ser personalizados; IDs ausentes são reservados pelo Organizador):

```json
{
  "pasta": "captador/entrada",
  "identificacao": {
    "prova": "Exame Nacional da Magistratura (ENAM)",
    "edicao": "2026.1",
    "caderno": "Tipo 1",
    "orgao": "ENFAM",
    "cargo": "Habilitação à magistratura (ENAM)",
    "banca": "FGV",
    "ano": "2026"
  },
  "situacao_gabarito": "definitivo",
  "situacao_inicial": 0
}
```

Executar `python digitalizador/pipeline.py --pedido pedido.json`. Substituir `pasta` por `prova_url` e `gabarito_url` para dois downloads diretos, ou por `urls` (lista) para páginas. A identificação informada se aplica a todas as reservas desse pedido; não usar uma identificação única de edição para uma lista de várias edições. O prefixo do arquivo não gera resposta nem tema.

Situação inicial 0 é a **política de cadastro declarada pela execução**, não uma conclusão sobre atualidade jurídica. Pode ser alterada para 1 com `--situacao-inicial 1`. Anulação reconhecida no gabarito gera situação 2. Desatualização continua sendo informada pelo usuário.

## GitHub

Abrir **Actions → Captar e digitalizar provas → Run workflow**. Informar a URL ou deixar URL vazia para usar a pasta do repositório. Os PDFs de uma pasta precisam estar disponíveis no commit; colocar arquivos somente no PC não os envia ao GitHub. O mesmo programa roda no runner Ubuntu, sem depender do desktop ligado ou de um harness ativo.

O workflow publica `acervo-processado`, com:

```text
base/                 # acervo completo consultável; dados, metadados e fontes
captador/             # reservas, originais, protocolos e encaminhamentos
digitalizador/       # resultados intermediários e PNGs das páginas
compilador/           # relações/grupos propostos do acervo
relatorio.json        # incorporado, já incorporado, incompleto ou pendente
pedido.json           # parâmetros usados
```

O runner é temporário; o artefato é o resultado persistido no GitHub, com retenção de **30 dias**. Baixar e fazer backup antes de expirar. Não há commit automático dos PDFs nem da base no repositório. Para continuar o acervo de uma execução anterior, preencher `continuar_execucao` com o ID daquela execução; o workflow restaura seu artefato antes de processar. Sem esse campo, parte do acervo versionado em `organizador/`. Não há sincronização implícita com o PC nem fusão de acervos que evoluíram separadamente.

Os campos do workflow são dados em variáveis de ambiente, sem interpolação em comandos shell. Ações usam acesso de leitura ao repositório; o programa não precisa de chave de modelo de IA. A opção automático de gabarito reconhece somente hashes previamente conferidos (nesta entrega, o definitivo ENAM 2026.1). Arquivos desconhecidos permanecem reservados até declaração da sua situação.

## Resultado e limites

- Perfil atual: ENAM/FGV Tipo 1, PDF textual, 80 questões com A–E e layout de gabarito reconhecido. Outros formatos são reservados e apresentados como pendentes quando não extraíveis.
- Originais PDF são copiados ao acervo por hash. Páginas com elementos visuais/vetoriais são preservadas integralmente em PNG para conferência; a posição exata de figuras dentro do texto ainda não é reconstruída.
- Disciplina vem do cabeçalho. Tema automático é **Não classificado**. Descritores por regras são propostas lexicais; classificação semântica permanece futura. O Compilador já registra semelhanças lexicais propostas.
- Falha de numeração, alternativas ou gabarito impede a incorporação. Complementos/retificações não interpretados também bloqueiam. Avisos sobre classificação e apresentação visual são preservados, sem declarar completude semântica.
- Repetir o mesmo PDF no mesmo órgão/cargo retorna o mapeamento existente, sem acrescentar questões. Outro gabarito para a mesma prova exige tratamento específico de versão; não sobrescreve respostas automaticamente.
- O código de saída é 0 para todas as reservas incorporadas/já existentes; 2 para execução parcial/pendências; 1 para erro de invocação. No Actions, pendências deixam a etapa com falha, mas o artefato é enviado mesmo assim.
- Atualizar uma reserva recebida anteriormente, suportar OCR e generalizar extratores não são resolvidos pela convenção dos nomes.

## Interrupção de gravação

O Organizador prepara e valida a base proposta antes de publicar. `.transacao-pendente.json` bloqueia consultas durante publicação parcial; `python -m basequestoes --base CAMINHO recuperar`, executado de `organizador/`, retoma os arquivos preservando os hashes esperados. Se o processo morreu e deixou `.base.lock`, confirmar que não existe mais um escritor antes de retirar apenas esse bloqueio. Não apagar o marcador nem `.transacoes/` para tentar liberar a base. Recuperação recusa sobrescrever alterações externas conflitantes.

Arquivos de trabalho são ignorados pelo Git. O funcionamento offline exige apenas PDFs locais e dependências já instaladas; uma URL naturalmente exige conexão no ambiente que executa o Captador.

O pipeline executa o [Compilador](../compilador/README.md) uma vez após as incorporações do pedido, sobre toda a base. Resultados lexicais são derivados e preservam as ocorrências. Falha na compilação deixa as questões incorporadas e aparece em compilacao no relatório; é possível recompilar sem novos downloads.

## Relatórios de execução

O pipeline publica o relatório por substituição atômica. Ao iniciar, marca em_execucao; erros de pedido/recepção geram estado falha e completo false, substituindo eventual relatório anterior. O adaptador GitHub também marca preparando antes de ler as entradas e registra falhas de preparação. Interrupções abruptas podem deixar estado intermediário, que nunca significa sucesso. A criação inicial da cópia da base no runner ocorre em pasta temporária, publicada somente depois de copiada.
