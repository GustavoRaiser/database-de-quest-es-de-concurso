"""Integração pública: pasta/URL -> captação -> extração -> acervo e repetição."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_digitalizador import documentos, ROOT

spec = importlib.util.spec_from_file_location('pipeline',ROOT/'digitalizador/pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class PipelineTest(unittest.TestCase):
    def test_pasta_ate_base_preserva_ids_e_nao_duplica(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base,inbox,cap,saida = [tmp/n for n in ('base','entrada','captador','saida')]
            base.mkdir();inbox.mkdir()
            for nome in ('manifesto.json','catalogos.json','indice.json'):
                shutil.copyfile(ROOT/'organizador'/nome,base/nome)
            prova,gab = documentos()
            (inbox/'enam-2026.1_cad.pdf').write_bytes(prova)
            (inbox/'enam-2026.1_gab.pdf').write_bytes(gab)
            entrada = {'pasta':str(inbox),'situacao_gabarito':'definitivo','situacao_inicial':1}
            r = pipeline.executar(entrada,cap,saida,base)
            self.assertTrue(r['completo'],r)
            self.assertEqual(r['resultados'][0]['novas_questoes'],80)
            arquivos = {p.relative_to(base):p.read_bytes() for p in (base/'dados').rglob('*') if p.is_file()}
            r2 = pipeline.executar(entrada,cap,saida,base)
            self.assertTrue(r2['completo'],r2)
            self.assertEqual(r2['resultados'][0]['novas_questoes'],0)
            self.assertEqual(arquivos,{p.relative_to(base):p.read_bytes() for p in (base/'dados').rglob('*') if p.is_file()})
            for p in (inbox/'enam-2026.1_cad.pdf',inbox/'enam-2026.1_gab.pdf'):
                self.assertTrue(p.exists())
            # Outra aplicação acrescenta ao fim do mesmo tema, preservando IDs.
            (inbox/'enam-2026.2_cad.pdf').write_bytes(prova.replace(b'2026.1',b'2026.2'))
            (inbox/'enam-2026.2_gab.pdf').write_bytes(gab)
            r3 = pipeline.executar(entrada,cap,saida,base)
            self.assertTrue(r3['completo'],r3)
            for path,raw in arquivos.items():
                if path.suffix == '.jsonl':
                    self.assertTrue((base/path).read_bytes().startswith(raw))
            m = json.loads(next((base/'dados').rglob('*_md.json')).read_text())
            self.assertEqual(len(m),160)
            self.assertTrue(all(v['gabarito']['alternativas_corretas']==[2] for k,v in m.items() if k not in ('42','122')))
            rows = next((base/'dados').rglob('*.jsonl')).read_text().splitlines()
            self.assertEqual(json.loads(rows[0])[0],1)
            self.assertEqual(json.loads(rows[41])[0],2)
            self.assertTrue((base/m['1']['origens'][0]['ficha_prova']).exists())
            p = subprocess.run([sys.executable,'-m','basequestoes','--base',str(base),'validar'],cwd=ROOT/'organizador',capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)['questoes'],160)
            # Retificação explícita não duplica a prova nem sobrescreve respostas já incorporadas.
            def captar(acao,dados=None):
                return pipeline.cli([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(cap),acao],dados)
            lote=next(m for m in captar('estado')['lotes'] if m['identificacao']['edicao']=='2026.1')
            (cap/'entrada/gab_novo.pdf').write_bytes(gab.replace(b'(B)',b'(C)'))
            lote=captar('anexar',{'lote':lote['id'],'tipo':'gabarito','nome':'gab_novo.pdf',
                                 'entrada':'gab_novo.pdf','situacao_gabarito':'definitivo'})
            captar('encaminhar',{'lote':lote['id'],'gabarito_sha256':lote['documentos'][-1]['sha256']})
            extracao=pipeline.cli([sys.executable,str(ROOT/'digitalizador/app.py'),'--captacoes',str(cap),
                                  '--saida',str(saida),'--base',str(base),lote['id']])
            antes={p.relative_to(base):p.read_bytes() for p in (base/'dados').rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError,'outro gabarito'):
                pipeline.cli([sys.executable,'-m','basequestoes','--base',str(base),'incorporar-extracao'],
                    {'resultado':str(saida/(extracao['resultado_id']+'.json')),'captacoes':str(cap),'situacao_inicial':0},ROOT/'organizador')
            self.assertEqual(antes,{p.relative_to(base):p.read_bytes() for p in (base/'dados').rglob('*') if p.is_file()})

    def test_par_incompleto_e_gabarito_sem_situacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);inbox=tmp/'entrada';inbox.mkdir();base=tmp/'base';base.mkdir()
            for nome in ('manifesto.json','catalogos.json','indice.json'):
                shutil.copyfile(ROOT/'organizador'/nome,base/nome)
            prova,gab=documentos()
            (inbox/'enam-2026.1_cad.pdf').write_bytes(prova)
            r=pipeline.executar({'pasta':str(inbox)},tmp/'cap',tmp/'saida',base)
            self.assertFalse(r['completo'])
            self.assertEqual(r['resultados'][0]['estado'],'aguardando_par')
            (inbox/'enam-2026.1_gab.pdf').write_bytes(gab)
            r=pipeline.executar({'pasta':str(inbox)},tmp/'cap',tmp/'saida',base)
            self.assertFalse(r['completo'])
            self.assertIn('situacao_gabarito',r['resultados'][0]['erro'])
            self.assertFalse(list((tmp/'cap'/'encaminhamentos').glob('*.json')))


if __name__=='__main__':unittest.main()
