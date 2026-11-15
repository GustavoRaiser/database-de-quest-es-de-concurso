# Digitalizador

Extrator local executado por código, sem modelos de IA. Primeiro perfil suportado: **ENAM/FGV Tipo 1**, 80 questões A–E, PDF com texto e gabarito no layout documentado. A extração gera candidatos para consulta e validação; ainda não incorpora questões ao acervo definitivo.

## Instalar e executar

Na raiz do repositório:

```sh
python -m pip install -r digitalizador/requirements.txt
python emissor/servidor.py --base organizador/exemplos/base
```

Abra http://127.0.0.1:8000 → Adicionar material. Registre prova/edição/caderno com códigos e nomes de órgão/cargo, banca e ano. Para o caderno testado, use prova ENAM, edição 2026.1, caderno Tipo 1 e ano 2026.

Envie os PDFs, escolha arquivos da pasta ou use Baixar PDF por URL. A busca de links de uma página reconhece os cartões da listagem pública de provas do Qconcursos; outros layouts podem não ser reconhecidos. Escolha a prova e o gabarito corretos e informe a condição preliminar/definitivo da fonte. Encaminhe o lote e clique **Processar ENAM Tipo 1 no computador**. O botão executa o extrator no host e apresenta o resultado e suas pendências. É possível baixar o JSON da prévia.

Sem prova e gabarito íntegros e vinculados, não há extração, inclusive por chamada direta. Um pacote obsoleto também é recusado. A edição/caderno informada precisa corresponder à capa suportada; a associação semântica do gabarito à edição continua sendo uma declaração do usuário.

## CLI

```sh
python captador/app.py --raiz captador/trabalho estado
python digitalizador/app.py --captacoes captador/trabalho --saida digitalizador/trabalho UUID-DO-LOTE
```

O lote precisa ter sido encaminhado antes. Os comandos públicos do Captador recebem JSON pela entrada padrão. O Digitalizador usa a operação entrega do Captador para verificar pacote e arquivos e registra a extração programática separadamente da análise manual do usuário.

## Saída

Ver [CONTRATO.md](CONTRATO.md). O JSON contém numeração e páginas originais, disciplina de cabeçalho, enunciado, alternativas, gabarito, descritores por regras e pendências. Arquivos ficam em digitalizador/trabalho/ (ignorados pelo Git). Configure --digitalizacoes no Emissor ou --saida na CLI para outro destino. Faça backup dessas pastas junto aos originais do Captador.

Não há IA nesta operação. Os descritores são produzidos pela CLI pública do Organizador, com vocabulário local e regras auditáveis; eles não comprovam conhecimento exigido ou equivalência entre questões. O texto original permanece disponível para conferência.

## Limites atuais

- Suporta o layout ENAM/FGV Tipo 1 implementado, não um leitor universal de provas.
- Falha explícita para numeração/alternativas incompletas e PDFs sem texto. OCR não implementado.
- Imagens e vetores no corpo são referenciados por página e geram pendências; não há reconstrução visual automática fiel.
- Gabaritos de outros tipos não são misturados ao Tipo 1. Anulação depende da legenda reconhecida.
- Retificações/complementos são preservados, mas ainda exigem interpretação separada.
- Temas, score de semelhança, agrupamentos, processamento de apostilas e incorporação no acervo não foram automatizados.
- A interface usa extraido_com_pendencias; não presume completude semântica nem atualidade jurídica.

## Verificar

```sh
python -m unittest discover -s digitalizador/tests -v
```

Os testes usam PDFs sintéticos. O [teste real atualizado](TESTE_PIPELINE_SEM_IA.md) registra o resultado com o ENAM 2026.1. O [diagnóstico anterior](TESTE_ENAM_2026_1.md) permanece como histórico da etapa em que o extrator ainda não integrava o repositório.
