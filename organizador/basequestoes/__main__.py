"""Uso: python -m basequestoes --base exemplos/base validar."""

import argparse
import json
import sys

from .core import Base, Erro, ler_json
from .emissao import emitir, FILTROS
from .abordagem import preparar, registrar


def main():
    parser = argparse.ArgumentParser(description="Questões, procedência e recursos locais (v3)")
    parser.add_argument("--base", default=".", help="pasta que contém manifesto.json")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("validar")
    sub.add_parser("catalogos")
    preparar_abordagem = sub.add_parser('preparar-abordagem')
    preparar_abordagem.add_argument('id')
    registrar_abordagens = sub.add_parser('registrar-abordagens')
    registrar_abordagens.add_argument('tema')
    registrar_abordagens.add_argument('arquivo')
    registrar_abordagens.add_argument('--substituir', action='store_true')
    emissao = sub.add_parser("emitir")
    for campo in FILTROS:
        emissao.add_argument("--" + campo, default="")
    emissao.add_argument("--pagina", type=int, default=1)
    emissao.add_argument("--por-pagina", type=int, default=20)
    consultar = sub.add_parser("consultar")
    consultar.add_argument("id")
    recurso = sub.add_parser("guardar-recurso")
    recurso.add_argument("arquivo")
    recurso.add_argument("--mime", required=True)
    metadados = sub.add_parser("registrar-metadados")
    metadados.add_argument("tema")
    metadados.add_argument("arquivo", help="objeto JSON com números de questões como chaves")
    lote = sub.add_parser("registrar-lote")
    lote.add_argument("arquivo", help="JSON com manifesto e relatorio de questões já cadastradas")
    args = parser.parse_args()
    try:
        base = Base(args.base)
        if args.comando == "validar":
            resultado = base.validar()
        elif args.comando == "catalogos":
            resultado = base.catalogos
        elif args.comando == 'preparar-abordagem':
            resultado = preparar(base, args.id)
        elif args.comando == 'registrar-abordagens':
            resultado = registrar(base, args.tema, ler_json(args.arquivo), args.substituir)
        elif args.comando == "emitir":
            resultado = emitir(base, {campo: getattr(args, campo) for campo in FILTROS}, args.pagina, args.por_pagina)
        elif args.comando == "consultar":
            resultado = base.consultar(args.id)
        elif args.comando == "guardar-recurso":
            resultado = base.guardar_recurso(args.arquivo, args.mime)
        elif args.comando == "registrar-metadados":
            resultado = {"registrados": base.registrar_metadados(args.tema, ler_json(args.arquivo))}
        else:
            entrada = ler_json(args.arquivo)
            if not isinstance(entrada, dict) or set(entrada) != {"manifesto", "relatorio"}:
                raise Erro("fornecer objeto com manifesto e relatorio")
            resultado = {"lote": base.registrar_lote(entrada["manifesto"], entrada["relatorio"])}
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0
    except (Erro, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
