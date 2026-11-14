"""Consulta pública paginada, sem alterar o acervo."""

from .core import exigir, linhas, registro


FILTROS = ("orgao", "cargo", "disciplina", "tema")
GRUPOS = ("orgaos", "cargos", "disciplinas", "temas")


def emitir(base, filtros, pagina=1, por_pagina=20):
    exigir(type(pagina) is int and pagina > 0, "página deve ser positiva")
    exigir(type(por_pagina) is int and 1 <= por_pagina <= 100, "por_pagina deve estar entre 1 e 100")
    for campo, grupo in zip(FILTROS, GRUPOS):
        exigir(not filtros.get(campo) or filtros[campo] in base.catalogos[grupo], f"filtro desconhecido: {campo}")
    total, itens, cache = 0, [], {}
    inicio = (pagina - 1) * por_pagina
    for tema, caminho in sorted(base.indice["temas"].items()):
        partes = tema.split(".")
        chaves = [".".join(partes[:n]) for n in range(1, 5)]
        if any(filtros.get(campo) and filtros[campo] != chave for campo, chave in zip(FILTROS, chaves)):
            continue
        for n, q in linhas(base.local(caminho)):
            registro(q)
            if inicio <= total < inicio + por_pagina:
                if tema not in cache:
                    cache[tema] = base.metadados(tema)
                itens.append({"id": f"{tema}.{n}", "questao": q,
                              "metadados": cache[tema].get(str(n)),
                              "classificacao": {campo: {"id": chave, "nome": base.catalogos[grupo][chave]}
                                                for campo, grupo, chave in zip(FILTROS, GRUPOS, chaves)}})
            total += 1
    return {"itens": itens, "total": total, "pagina": pagina, "por_pagina": por_pagina,
            "paginas": (total + por_pagina - 1) // por_pagina}
