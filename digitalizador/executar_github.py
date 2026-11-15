"""Adaptador do workflow. Entradas em variáveis, nunca interpoladas em shell."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    trabalho = ROOT/'digitalizador/trabalho/github'
    trabalho.mkdir(parents=True,exist_ok=True)
    base = trabalho/'base'
    if not base.exists():
        base.mkdir()
        for nome in ('manifesto.json','catalogos.json','indice.json','dados','recursos','importacoes','provas'):
            src = ROOT/'organizador'/nome
            if src.is_dir():shutil.copytree(src,base/nome)
            elif src.is_file():shutil.copyfile(src,base/nome)
    pedido = {'identificacao':json.loads(os.environ.get('IDENTIFICACAO','') or '{}'),
              'situacao_inicial':int(os.environ.get('SITUACAO_INICIAL','0'))}
    url = os.environ.get('FONTE_URL','').strip()
    if url:
        pedido['urls'] = [u.strip() for u in url.splitlines() if u.strip()]
    else:
        pasta = (ROOT/os.environ.get('PASTA_ENTRADA','captador/entrada')).resolve()
        if not pasta.is_relative_to(ROOT) or pasta == ROOT:
            raise ValueError('Pasta de entrada deve estar dentro do repositório')
        pedido['pasta'] = str(pasta)
    situacao = os.environ.get('SITUACAO_GABARITO','automatico')
    if situacao != 'automatico':pedido['situacao_gabarito'] = situacao
    arquivo = trabalho/'pedido.json'
    arquivo.write_text(json.dumps(pedido,ensure_ascii=False),encoding='utf-8')
    cmd = [sys.executable,str(ROOT/'digitalizador/pipeline.py'),'--pedido',str(arquivo),
           '--captacoes',str(trabalho/'captador'),'--saida',str(trabalho/'digitalizador'),
           '--base',str(base),'--relatorio',str(trabalho/'relatorio.json')]
    resultado = subprocess.run(cmd)
    resumo = Path(os.environ['GITHUB_STEP_SUMMARY']) if os.environ.get('GITHUB_STEP_SUMMARY') else None
    if resumo and (trabalho/'relatorio.json').exists():
        r=json.loads((trabalho/'relatorio.json').read_text(encoding='utf-8'))
        with resumo.open('a',encoding='utf-8') as f:
            f.write('## Captação e digitalização\n\n')
            f.write('Resultado disponível no artefato **acervo-processado**.\n\n')
            f.write('```json\n'+json.dumps({'contagens':r['contagens'],'completo':r['completo']},ensure_ascii=False,indent=2)+'\n```\n')
    return resultado.returncode


if __name__=='__main__':sys.exit(main())
