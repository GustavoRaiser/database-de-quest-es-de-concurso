"""Consulta pública paginada, sem alterar o acervo."""

from .core import exigir, linhas, registro
from .core import ler_json
import hashlib
import json


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


def exportar(base, filtros):
    """Snapshot público em uma leitura, para consumidores como o Compilador."""
    with base.bloqueio():
        return _snapshot(base,filtros)


def _snapshot(base,filtros):
    base.validar()
    for campo,grupo in zip(FILTROS,GRUPOS):
        exigir(not filtros.get(campo) or filtros[campo] in base.catalogos[grupo], f'filtro desconhecido: {campo}')
    itens=[]
    for tema,caminho in sorted(base.indice['temas'].items()):
        partes=tema.split('.')
        chaves=['.'.join(partes[:n]) for n in range(1,5)]
        if any(filtros.get(campo) and filtros[campo]!=chave for campo,chave in zip(FILTROS,chaves)):
            continue
        metadados=base.metadados(tema)
        classificacao={campo:{'id':chave,'nome':base.catalogos[grupo][chave]}
                       for campo,grupo,chave in zip(FILTROS,GRUPOS,chaves)}
        for n,q in linhas(base.local(caminho)):
            itens.append({'id':f'{tema}.{n}','questao':q,'metadados':metadados.get(str(n)),
                          'classificacao':classificacao})
    fichas = {}
    for item in itens:
        for origem in (item['metadados'] or {}).get('origens',[]):
            ref = origem.get('ficha_prova')
            if ref and ref not in fichas:
                fichas[ref] = ler_json(base.local(ref))
    snapshot = {'versao':1,'manifesto':base.manifesto,'itens':itens,'provas':fichas}
    base.conferir_leitura()
    canonico=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n'
    return dict(snapshot, corpus_sha256=hashlib.sha256(canonico.encode()).hexdigest())
