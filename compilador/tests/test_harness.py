import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
import harness
from test_compilador import ROOT,CONFIG


class HarnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.raiz=Path(self.tmp.name)
        self.base=self.raiz/'base';shutil.copytree(ROOT/'organizador/exemplos/base',self.base)
        self.saida=self.raiz/'compilador'
    def tearDown(self):self.tmp.cleanup()
    def preparar(self):return harness.preparar(self.base,self.saida,CONFIG,pares=[['N32.a2.5.y.1','N32.a2.5.y.2']])
    def resposta(self,j):
        tid=j['proximas'][0]['tarefa_id'];t=harness.ler(j['proximas'][0]['arquivo'])
        return {'tarefa_id':tid,'autor':'Harness de teste','modelo':{'nome':'modelo simulado','provedor':'teste'},
                'dimensoes':{k:{'score':70,'justificativa':'Teste de contrato, não avaliação real.',
                  'trecho_a':t['a']['questao'][1],'trecho_b':t['b']['questao'][1]} for k in CONFIG['pesos']},'avisos':['Teste sintético.']}
    def test_preparacao_registro_consolidacao_e_preservacao(self):
        antes={p.relative_to(self.base):p.read_bytes() for p in self.base.rglob('*') if p.is_file()}
        with patch('semantica.Ollama',side_effect=AssertionError('Não chamar IA local')):
            j=self.preparar();self.assertEqual(j['pendentes'],1)
            parcial=harness.consolidar(self.base,self.saida,j['lote']);self.assertFalse(parcial['completo'])
            r=self.resposta(j);harness.registrar(self.base,self.saida,j['lote'],r)
            pronto=harness.consolidar(self.base,self.saida,j['lote']);self.assertTrue(pronto['completo'])
            self.assertEqual(harness.registrar(self.base,self.saida,j['lote'],r)['registradas'],1)
            self.assertEqual(self.preparar()['pendentes'],0)
            sem=app.consultar(self.saida/'semantica_harness',pronto['id'])
            self.assertEqual(sem['avaliacoes_harness'][0]['modelo_declarado']['nome'],'modelo simulado')
            self.assertEqual(len(sem['pares']),1)
        self.assertTrue((self.saida/'ultimo.json').exists())
        self.assertEqual(antes,{p.relative_to(self.base):p.read_bytes() for p in self.base.rglob('*') if p.is_file()})
    def test_rejeita_citacao_inventada_e_nao_registra_parcialmente(self):
        j=self.preparar();r=self.resposta(j);r['dimensoes']['conteudo']['trecho_a']='não existe na questão'
        with self.assertRaises(ValueError):harness.registrar(self.base,self.saida,j['lote'],r)
        self.assertEqual(harness.estado(self.saida,j['lote'])['registradas'],0)
    def test_rejeita_tarefa_trocada_e_corpus_alterado(self):
        j=self.preparar();r=self.resposta(j);r['tarefa_id']='a'*64
        with self.assertRaises(ValueError):harness.registrar(self.base,self.saida,j['lote'],r)
        r=self.resposta(j)
        with (self.base/'dados/N32/a2/5/y.jsonl').open('a') as f:f.write('[0,"Outra questão",[]]\n')
        with self.assertRaisesRegex(ValueError,'Base mudou'):harness.registrar(self.base,self.saida,j['lote'],r)
        with self.assertRaisesRegex(ValueError,'Base mudou'):harness.consolidar(self.base,self.saida,j['lote'])
    def test_substituicao_explicita_preserva_recibos(self):
        j=self.preparar();r=self.resposta(j);harness.registrar(self.base,self.saida,j['lote'],r)
        novo=copy.deepcopy(r);novo['dimensoes']['conteudo']['score']=60
        with self.assertRaises(ValueError):harness.registrar(self.base,self.saida,j['lote'],novo)
        harness.registrar(self.base,self.saida,j['lote'],novo,substituir=True)
        self.assertEqual(len(list((self.saida/'harness'/j['lote']/'respostas'/r['tarefa_id']).glob('*.json'))),2)
    def test_recibo_corrompido_bloqueia_consolidacao(self):
        j=self.preparar();r=self.resposta(j);harness.registrar(self.base,self.saida,j['lote'],r)
        p=next((self.saida/'harness'/j['lote']/'respostas').glob('*/*.json'));p.write_text('{}')
        with self.assertRaises(ValueError):harness.consolidar(self.base,self.saida,j['lote'])
    def test_cli_semantica_prioriza_harness_e_local_bloqueado(self):
        cmd=[sys.executable,str(ROOT/'compilador/app.py'),'--base',str(self.base),'--saida',str(self.saida),'semantica']
        p=subprocess.run(cmd,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['provedor'],'harness')
        p=subprocess.run(cmd+['--provedor','local'],text=True,capture_output=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('desabilitada',p.stderr)
    def test_registro_em_lote_atomico(self):
        j=harness.preparar(self.base,self.saida,CONFIG,exaustivo=True)
        primeiro=self.resposta(j)
        j2=copy.deepcopy(j);j2['proximas']=j['proximas'][1:];segundo=self.resposta(j2)
        segundo['modelo']={}
        with self.assertRaises(ValueError):harness.registrar(self.base,self.saida,j['lote'],[primeiro,segundo])
        self.assertEqual(harness.estado(self.saida,j['lote'])['registradas'],0)

if __name__=='__main__':unittest.main()
