"""Orquestra CLIs públicas. Mesmo executável em desktop, harness e GitHub Actions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def cli(cmd, dados=None, cwd=None):
    p = subprocess.run(cmd,input=json.dumps(dados,ensure_ascii=False),capture_output=True,text=True,
                       encoding='utf-8',cwd=cwd,timeout=1800)
    if p.returncode:
        raise ValueError(p.stderr.strip() or 'Comando falhou')
    return json.loads(p.stdout)


def executar(entrada, captacoes, saida, base):
    captacoes,saida,base = (Path(p).resolve() for p in (captacoes,saida,base))
    def cap(acao,dados):
        return cli([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(captacoes),acao],dados)
    def org(acao,dados):
        return cli([sys.executable,'-m','basequestoes','--base',str(base),acao],dados,ROOT/'organizador')
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
    return {'versao':1,'ambiente':'execução local ao processo; sem chamadas a modelos',
            'captacoes':str(captacoes),'base':str(base),'resultados':resultados,
            'contagens':contagens,'erros_recepcao':recebidos['erros'],
            'completo':bool(resultados) and not recebidos['erros'] and all(r['estado'] in ('incorporado','ja_incorporado') for r in resultados)}


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
    args = p.parse_args()
    try:
        entrada = json.loads(args.pedido.read_text(encoding='utf-8')) if args.pedido else {}
        if args.url: entrada['urls'] = args.url
        if args.pasta: entrada['pasta'] = str(args.pasta.resolve())
        if args.situacao_gabarito: entrada['situacao_gabarito'] = args.situacao_gabarito
        if args.situacao_inicial is not None: entrada['situacao_inicial'] = args.situacao_inicial
        if not any(entrada.get(k) for k in ('urls','pasta','prova_url','gabarito_url')):
            raise ValueError('Informar --url, --pasta ou --pedido')
        r = executar(entrada,args.captacoes,args.saida,args.base)
        args.relatorio.parent.mkdir(parents=True,exist_ok=True)
        args.relatorio.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(r,ensure_ascii=False,indent=2))
        return 0 if r['completo'] else 2
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        print('Erro: '+str(exc),file=sys.stderr)
        return 1


if __name__ == '__main__': sys.exit(main())
