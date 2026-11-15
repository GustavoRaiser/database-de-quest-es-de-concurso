# Entrada por pasta

Coloque pares `NOME_cad.pdf` e `NOME_gab.pdf` aqui, ou indique outra pasta com `--pasta`.
O mesmo prefixo declara que caderno e gabarito formam um par; nada é apagado.
Arquivos locais PDF desta pasta são ignorados pelo Git. Para rodar no GitHub, prefira URL no workflow; se escolher enviar os PDFs ao repositório, eles precisam efetivamente estar no commit disponível ao runner.

Nomes como `enam-2026.1_cad.pdf` permitem propor a identificação do perfil ENAM. Para outros nomes, fornecer identificação em JSON; o nome não comprova a edição, o tipo do caderno ou se o gabarito é definitivo. Ver [operação portátil](../../digitalizador/OPERACAO.md).
