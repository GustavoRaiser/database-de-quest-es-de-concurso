"""Orquestra CLIs públicas. Mesmo executável em desktop, harness e GitHub Actions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import os
import tempfile
from datetime import datetime, timezone


def gravar_relatorio(path, dados):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(dados,f,ensure_ascii=False,indent=2)
            f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

ROOT = Path(__file__).resolve().parents[1]


def cli(cmd, dados=None, cwd=None):
    p = subprocess.run(cmd,input=json.dumps(dados,ensure_ascii=False),capture_output=True,text=True,
                       encoding='utf-8',cwd=cwd,timeout=1800)
    if p.returncode:
        raise ValueError(p.stderr.strip() or 'Comando falhou')
    return json.loads(p.stdout)


def executar(entrada, captacoes, saida, base, compilacoes=None):
    captacoes,saida,base = (Path(p).resolve() for p in (captacoes,saida,base))
    def cap(acao,dados):
        return cli([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(captacoes),acao],dados)
    def org(acao,dados):
        return cli([sys.executable,'-m','basequestoes','--base',str(base),acao],dados,ROOT/'organizador')
    modo=entrada.get('analise_semantica','harness')
    if modo not in ('harness','local','nenhuma'):raise ValueError('Modo semântico inválido')
    if modo=='local' and entrada.get('habilitar_ia_local') is not True:
        raise ValueError('IA local exige habilitar_ia_local=true por autorização expressa')
    if modo!='local' and entrada.get('semantica'):
        raise ValueError('Configuração local exige analise_semantica=local e habilitação explícita')
    recebidos = cap('receber',entrada)
    resultados = []
    for reserva in recebidos['reservas']:
        item = {'reserva':reserva['id'],'titulo':reserva['titulo']}
        try:
            if reserva['estado'] != 'par_reservado':
                item.update(estado='aguardando_par',erros=reserva['erros'])
                resultados.append(item)
                continue
            ident = dict(reserva.get('identificacao_sugerida',{}))
            ident.pop('identificacao_proposta',None)
            ident.update(entrada.get('identificacao',{}))
            for campo in ('prova','edicao','caderno','orgao','cargo','banca','ano'):
                if not ident.get(campo):
                    raise ValueError('Informar identificacao.'+campo+' para a reserva')
            codigos = org('reservar-identidade',ident)
            ident.update(codigos)
            lote = cap('preparar-reserva',{'reserva':reserva['id'],'identificacao':ident,
                                         'situacao_gabarito':entrada.get('situacao_gabarito')})
            item.update(lote)
            r = cli([sys.executable,str(ROOT/'digitalizador/app.py'),'--captacoes',str(captacoes),
                     '--saida',str(saida),'--base',str(base),lote['lote']])
            item['extracao'] = r['resultado_id']
            if r.get('bloqueios'):
                item.update(estado='bloqueado',bloqueios=r['bloqueios'])
            else:
                incorporacao = org('incorporar-extracao',{'resultado':str(saida/(r['resultado_id']+'.json')),
                    'captacoes':str(captacoes),'situacao_inicial':entrada.get('situacao_inicial',0)})
                item.update(incorporacao)
        except (ValueError,OSError,subprocess.SubprocessError) as exc:
            item.update(estado='pendente',erro=str(exc))
        resultados.append(item)
    contagens = {}
    for r in resultados:
        contagens[r['estado']] = contagens.get(r['estado'],0)+1
    compilacao={'estado':'nao_executada'}
    if any(r['estado'] in ('incorporado','ja_incorporado') for r in resultados):
        try:
            pasta_compilador=Path(compilacoes or ROOT/'compilador/trabalho').resolve()
            c=cli([sys.executable,str(ROOT/'compilador/app.py'),'--base',str(base),
                   '--saida',str(pasta_compilador),'analisar'])
            if modo=='local':
                h=cli([sys.executable,str(ROOT/'compilador/app.py'),'--base',str(base),
                       '--saida',str(pasta_compilador),'semantica','--provedor','local','--habilitar-ia-local',
                       '--config',str(Path(entrada.get('semantica') or ROOT/'compilador/semantica.json').resolve())])
                c['semantica_registro']=h['registro']
            elif modo=='harness':
                c['harness']=cli([sys.executable,str(ROOT/'compilador/app.py'),'--base',str(base),
                                  '--saida',str(pasta_compilador),'preparar-tarefas'])
            compilacao={'estado':'compilado','id':c['id'],'arquivo':c['arquivo'],
                        'corpus_sha256':c['corpus_sha256'],'diagnostico':c['diagnostico'],'semantica_registro':c.get('semantica_registro'),'harness':c.get('harness')}
        except (ValueError,OSError,subprocess.SubprocessError) as exc:
            compilacao={'estado':'falha','erro':str(exc)}
    return {'versao':1,'ambiente':'execução local; IA somente no Compilador quando configurada',
            'captacoes':str(captacoes),'base':str(base),'resultados':resultados,
            'contagens':contagens,'erros_recepcao':recebidos['erros'],'compilacao':compilacao,
            'analise_semantica':modo,
            'semantica_concluida':(compilacao.get('harness') or {}).get('pendentes',1)==0 if modo=='harness' else modo=='local' and compilacao['estado']=='compilado',
            'completo':bool(resultados) and not recebidos['erros'] and compilacao['estado']=='compilado' and all(r['estado'] in ('incorporado','ja_incorporado') for r in resultados)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',action='append',default=[],help='listagem Qconcursos; pode repetir')
    p.add_argument('--pasta',type=Path,help='pasta com pares NOME_cad.pdf e NOME_gab.pdf')
    p.add_argument('--pedido',type=Path,help='JSON com urls/prova_url/gabarito_url/identificacao e opções')
    p.add_argument('--situacao-gabarito',choices=('preliminar','definitivo'))
    p.add_argument('--situacao-inicial',type=int,choices=(0,1),default=None)
    p.add_argument('--captacoes',type=Path,default=ROOT/'captador/trabalho')
    p.add_argument('--saida',type=Path,default=ROOT/'digitalizador/trabalho')
    p.add_argument('--base',type=Path,default=ROOT/'organizador')
    p.add_argument('--relatorio',type=Path,default=ROOT/'digitalizador/trabalho/pipeline.json')
    p.add_argument('--compilacoes',type=Path,default=ROOT/'compilador/trabalho')
    p.add_argument('--analise-semantica',choices=('harness','local','nenhuma'))
    p.add_argument('--habilitar-ia-local',action='store_true')
    p.add_argument('--semantica',type=Path,help='configuração opcional de IA local exclusiva do Compilador')
    args = p.parse_args()
    try:
        gravar_relatorio(args.relatorio,{'versao':1,'estado':'em_execucao','completo':False,
                                        'iniciado_em':datetime.now(timezone.utc).isoformat()})
        entrada = json.loads(args.pedido.read_text(encoding='utf-8')) if args.pedido else {}
        if not isinstance(entrada,dict):raise ValueError('Pedido deve ser objeto JSON')
        if not isinstance(entrada.get('identificacao',{}),dict):raise ValueError('Identificação deve ser objeto JSON')
        if args.analise_semantica: entrada['analise_semantica']=args.analise_semantica
        if args.habilitar_ia_local: entrada['habilitar_ia_local']=True
        if args.semantica: entrada['semantica']=str(args.semantica.resolve())
        if args.url: entrada['urls'] = args.url
        if args.pasta: entrada['pasta'] = str(args.pasta.resolve())
        if args.situacao_gabarito: entrada['situacao_gabarito'] = args.situacao_gabarito
        if args.situacao_inicial is not None: entrada['situacao_inicial'] = args.situacao_inicial
        if not any(entrada.get(k) for k in ('urls','pasta','prova_url','gabarito_url')):
            raise ValueError('Informar --url, --pasta ou --pedido')
        r = executar(entrada,args.captacoes,args.saida,args.base,args.compilacoes)
        gravar_relatorio(args.relatorio,r)
        print(json.dumps(r,ensure_ascii=False,indent=2))
        return 0 if r['completo'] else 2
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        try:
            gravar_relatorio(args.relatorio,{'versao':1,'estado':'falha','completo':False,'erro':str(exc)})
        except OSError:
            pass
        print('Erro: '+str(exc),file=sys.stderr)
        return 1


if __name__ == '__main__': sys.exit(main())
