"""Compilador de relações entre questões. Biblioteca padrão; modo lexical e modo IA local opcional."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from motor import Motor, canon, digest, validar_config

ROOT=Path(__file__).resolve().parents[1]
FILTROS=('orgao','cargo','disciplina','tema')


def exportar(base,filtros):
    cmd=[sys.executable,'-m','basequestoes','--base',str(Path(base).resolve()),'exportar']
    for campo,valor in filtros.items():
        if valor:cmd.extend(['--'+campo,valor])
    p=subprocess.run(cmd,cwd=ROOT/'organizador',capture_output=True,text=True,encoding='utf-8',timeout=1800)
    if p.returncode:raise ValueError(p.stderr.strip() or 'Exportação falhou')
    snapshot=json.loads(p.stdout)
    conteudo={k:v for k,v in snapshot.items() if k!='corpus_sha256'}
    esperado=digest(conteudo)
    if snapshot.get('versao')!=1 or snapshot.get('corpus_sha256')!=esperado:
        raise ValueError('Snapshot incompatível ou corrompido')
    return snapshot


def atomico(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def salvar(resultado,saida,base):
    saida,base=Path(saida).resolve(),Path(base).resolve()
    if saida.is_relative_to(base):raise ValueError('Saída do Compilador deve ficar fora da base do Organizador')
    saida.mkdir(parents=True,exist_ok=True)
    lock=saida/'.compilador.lock'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as exc:raise ValueError('Compilador em gravação; conferir processo antes de retirar bloqueio') from exc
    try:
        os.close(fd)
        id_=digest(resultado);path=saida/(id_+'.json');raw=canon(resultado).encode()
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Resultado existente corrompido')
        if not path.exists():atomico(path,raw)
        atomico(saida/'ultimo.json',canon({'id':id_,'arquivo':id_+'.json','corpus_sha256':resultado['corpus_sha256']}).encode())
    finally:
        lock.unlink()
    return dict(resultado,id=id_,arquivo=str(path))


def consultar(saida,id_):
    if not re.fullmatch('[a-f0-9]{64}',id_):raise ValueError('ID de compilação inválido')
    raiz=Path(saida).resolve();path=raiz/(id_+'.json')
    if not path.resolve().is_relative_to(raiz):raise ValueError('Resultado fora da pasta de trabalho')
    resultado=json.loads(path.read_text(encoding='utf-8'))
    if resultado.get('versao')!=1 or digest(resultado)!=id_:raise ValueError('Resultado corrompido/incompatível')
    return dict(resultado,id=id_,arquivo=str(path))


def compilar(base,saida,config,filtros=None,exaustivo=False):
    filtros=filtros or {}
    snapshot=exportar(base,filtros)
    motor=Motor(snapshot,config)
    implementacao=digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(__file__).with_name('motor.py'))})
    resultado={'versao':1,'algoritmo':'lexical/2','implementacao_sha256':implementacao,
        'corpus_sha256':snapshot['corpus_sha256'],'configuracao':config,'criterios_sha256':digest(config),
        'filtros':{k:v for k,v in filtros.items() if v},'estado':'proposta_lexical',
        'limitacoes':['Os quatro critérios usam indicadores lexicais; score não é probabilidade nem equivalência semântica.',
                      'Ausência de um par no relatório não demonstra ausência de semelhança.',
                      'Grupos não contam ocorrências históricas; cadernos/aplicações não foram deduplicados.',
                      'Figuras, fórmulas visuais e tabelas em recursos não são interpretadas.'],
        'provas':snapshot['provas'],**motor.analisar(exaustivo)}
    return salvar(resultado,saida,base)


def compilar_hibrido(base,saida,config,semconfig,filtros=None,exaustivo=False,backend=None):
    from datetime import datetime,timezone
    from uuid import uuid4
    from semantica import MotorSemantico,Ollama
    lexical=compilar(base,saida,config,filtros,exaustivo)
    registro={'versao':1,'inicio':datetime.now(timezone.utc).isoformat(),
              'lexical':{'id':lexical['id'],'arquivo':lexical['arquivo'],'estado':'concluida'},
              'semantica':{'estado':'em_execucao'},'completo':False}
    path=Path(saida)/'registros'/(uuid4().hex+'.json')
    def gravar(p,d):atomico(p,canon(d).encode())
    gravar(path,registro)
    try:
        snapshot=exportar(base,filtros or {})
        if snapshot['corpus_sha256']!=lexical['corpus_sha256']:raise ValueError('Base mudou entre as análises; repetir')
        backend=backend or Ollama(semconfig)
        motor=MotorSemantico(snapshot,config,semconfig,backend,Path(saida)/'cache_ia',gravar)
        analise=motor.analisar(exaustivo)
        impl=digest({n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ('app.py','motor.py','semantica.py')})
        resultado={'versao':1,'algoritmo':'semantica_local/1','estado':'proposta_semantica_ia',
                   'corpus_sha256':snapshot['corpus_sha256'],'implementacao_sha256':impl,
                   'analise_lexical_id':lexical['id'],'criterios_sha256':digest(config),'configuracao':config,'semantica_configuracao':semconfig,
                   'filtros':filtros or {},'provas':snapshot['provas'],**analise}
        # Ponteiros próprios: uma compilação semântica nunca substitui ultimo.json lexical.
        sem=salvar(resultado,Path(saida)/'semantica',base)
        registro['semantica']={'estado':'parcial' if analise['pendencias_ia'] else 'concluida',
                              'id':sem['id'],'arquivo':sem['arquivo'],'processamento_ia':analise['processamento_ia'],
                              'pendencias':analise['pendencias_ia'],'modelos':backend.modelos}
        registro['completo']=not analise['pendencias_ia']
    except (ValueError,OSError,KeyError,TypeError) as exc:
        registro['semantica']={'estado':'falha','erro':str(exc)}
    registro['fim']=datetime.now(timezone.utc).isoformat();gravar(path,registro)
    return dict(registro,registro=str(path))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'organizador')
    p.add_argument('--saida',type=Path,default=Path(__file__).parent/'trabalho')
    p.add_argument('--criterios',type=Path,default=Path(__file__).with_name('criterios.json'))
    sub=p.add_subparsers(dest='comando',required=True)
    analisar=sub.add_parser('analisar',help='compara candidatas, propõe grupos e salva resultado derivado')
    comparar=sub.add_parser('comparar',help='compara um par explicitamente, sem limitar candidatas')
    comparar.add_argument('a');comparar.add_argument('b')
    similares=sub.add_parser('similares',help='busca questões relacionadas a um ID')
    similares.add_argument('id');similares.add_argument('--limite',type=int,default=10)
    semantico=sub.add_parser('semantica',help='executa análises lexical e IA local separadas')
    semantico.add_argument('--config',type=Path,default=Path(__file__).with_name('semantica.json'))
    semantico.add_argument('--exaustivo',action='store_true')
    consulta=sub.add_parser('consultar',help='lê compilação arquivada pelo hash')
    consulta.add_argument('id')
    for parser in (analisar,comparar,similares,semantico):
        for campo in FILTROS:parser.add_argument('--'+campo,default='')
    for parser in (analisar,similares):parser.add_argument('--exaustivo',action='store_true')
    args=p.parse_args()
    try:
        if args.comando=='consultar':resultado=consultar(args.saida,args.id)
        else:
            config=json.loads(args.criterios.read_text(encoding='utf-8'))
            validar_config(config)
            filtros={k:getattr(args,k) for k in FILTROS}
            if args.comando=='semantica':
                resultado=compilar_hibrido(args.base,args.saida,config,json.loads(args.config.read_text(encoding='utf-8')),filtros,args.exaustivo)
            elif args.comando=='analisar':resultado=compilar(args.base,args.saida,config,filtros,args.exaustivo)
            else:
                snapshot=exportar(args.base,filtros);motor=Motor(snapshot,config)
                if args.comando=='comparar':
                    resultado={'corpus_sha256':snapshot['corpus_sha256'],'configuracao':config,
                               'par':motor.comparar(motor.indice(args.a),motor.indice(args.b))}
                else:
                    if not 1<=args.limite<=1000:raise ValueError('Limite deve estar entre 1 e 1000')
                    i=motor.indice(args.id)
                    if args.exaustivo:candidatas=[j for j in range(len(motor.itens)) if j!=i];truncado=False
                    else:candidatas,truncado=motor.candidatas(i)
                    pares=sorted((motor.comparar(i,j) for j in candidatas),key=lambda par:(-par['score'],par['a'],par['b']))
                    resultado={'corpus_sha256':snapshot['corpus_sha256'],'questao':args.id,'pares':pares[:args.limite],
                               'candidatas_comparadas':len(candidatas),'busca_truncada':truncado,
                               'exaustivo':args.exaustivo,'criterios_sha256':digest(config)}
        print(json.dumps(resultado,ensure_ascii=False,indent=2))
        if args.comando=='semantica' and not resultado['completo']:
            print('Análise semântica incompleta; registro: '+resultado['registro'],file=sys.stderr)
            return 2
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        print('Erro: '+str(exc),file=sys.stderr);return 1


if __name__=='__main__':sys.exit(main())
