import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'compilador'))
from motor import Motor, validar_config
import app

CONFIG=json.loads((ROOT/'compilador/criterios.json').read_text())


def item(n,texto,assertivas=None,meta=None):
    return {'id':f'0.0.0.0.{n}','questao':[0,texto,assertivas or []],'metadados':meta,'classificacao':{}}


def motor(itens,**opcoes):
    c=copy.deepcopy(CONFIG);c.update(opcoes)
    return Motor({'itens':itens},c)


class MotorTest(unittest.TestCase):
    def test_texto_identico_sem_raciocinio_nao_inventa_dimensao(self):
        m=motor([item(1,'O contrato de compra pode ser anulado por vício.'),item(2,'O contrato de compra pode ser anulado por vício.')])
        p=m.comparar(0,1)
        self.assertEqual(p['score'],100)
        self.assertIsNone(p['dimensoes']['raciocinio'])
        self.assertEqual(p['cobertura'],0.8)
        self.assertEqual(p['estado'],'proposta_lexical')
        self.assertEqual(len(m.analisar()['grupos']),1)

    def test_assuntos_distintos_nao_agrupam(self):
        m=motor([item(1,'Constituição organiza poderes legislativo judiciário.'),item(2,'Fotossíntese produz glicose luz clorofila.')])
        self.assertEqual(m.comparar(0,1)['score'],0)
        self.assertEqual(m.analisar(exaustivo=True)['grupos'],[])

    def test_indeterminado_nao_e_coincidencia(self):
        p={'conceitos':['Não identificado'],'raciocinio':'indeterminado','estado':'declarada','geracao':'humano',
           'conteudo_exigido':'Não identificado.','recorte_especifico':'Não determinado.','pendencias':[]}
        m=motor([item(1,'azul',meta={'abordagem':p}),item(2,'verde',meta={'abordagem':p})])
        r=m.comparar(0,1)
        self.assertEqual(r['score'],0)
        self.assertIsNone(r['dimensoes']['raciocinio'])
        self.assertEqual(r['evidencias']['conceitos_comuns'],[])

    def test_conceitos_ajudam_busca_com_redacoes_distintas(self):
        p={'conceitos':['Contratos'],'raciocinio':'aplicar_regra','estado':'proposta','geracao':'regras','pendencias':['proposta']}
        m=motor([item(1,'Compra venda imóveis.',meta={'abordagem':p}),item(2,'Locação garante prestação.',meta={'abordagem':p})])
        self.assertEqual(m.candidatas(0)[0],[1])
        self.assertEqual(m.comparar(0,1)['dimensoes']['raciocinio'],100)
        self.assertTrue(any('propostos' in a for a in m.comparar(0,1)['avisos']))

    def test_negacao_e_visuais_permanecem_explicitos(self):
        m=motor([item(1,'Assinale a exceção ao contrato.',meta={'recursos':[{'arquivo':'original'}]}),
                 item(2,'Assinale o que não pertence ao contrato.')])
        avisos=m.comparar(0,1)['avisos']
        self.assertTrue(any('visuais' in x for x in avisos))
        self.assertTrue(any('negação' in x for x in avisos))

    def test_nao_propaga_igualdade_por_cadeia(self):
        m=motor([item(1,'contrato consumidor prazo nulidade'),
                 item(2,'contrato consumidor prazo nulidade licitacao servidor improbidade'),
                 item(3,'licitacao servidor improbidade')],limiar=0,limiar_grupo=40)
        r=m.analisar(exaustivo=True)
        self.assertGreaterEqual(m.comparar(0,1)['score'],40)
        self.assertGreaterEqual(m.comparar(1,2)['score'],40)
        self.assertLess(m.comparar(0,2)['score'],40)
        self.assertTrue(r['grupos'])
        self.assertTrue(all(len(g['questoes'])==2 for g in r['grupos']))

    def test_500_questoes_reduzem_comparacoes(self):
        itens=[item(n+1,f'Analise assunto{n//10} norma{n//10} prazo{n//10}.') for n in range(500)]
        r=motor(itens).analisar()
        self.assertEqual(r['diagnostico']['pares_possiveis'],124750)
        self.assertLess(r['diagnostico']['pares_comparados'],124750//4)
        self.assertEqual(len(r['grupos']),50)
        self.assertTrue(all(len(g['questoes'])==10 for g in r['grupos']))

    def test_limite_e_exaustivo_reportam_cobertura(self):
        m=motor([item(i,'mesmo contrato garantia prazo') for i in range(1,8)],vizinhos=1,max_postagem=2)
        r=m.analisar();e=m.analisar(exaustivo=True)
        self.assertTrue(r['diagnostico']['buscas_truncadas'])
        self.assertGreater(r['diagnostico']['pares_nao_comparados'],0)
        self.assertEqual(e['diagnostico']['pares_comparados'],21)
        self.assertEqual(e['diagnostico']['pares_nao_comparados'],0)

    def test_base_vazia_e_solitario(self):
        for itens in ([],[item(1,'Contrato de locação.')]):
            r=motor(itens).analisar()
            self.assertEqual(r['pares'],[])
            self.assertEqual(r['grupos'],[])

    def test_criterios_invalidos(self):
        for alteracao in ({'vizinhos':0},{'limiar_grupo':10},{'cobertura_minima':0},{'limiar':False},{'pesos':list(CONFIG['pesos'])},{'pesos':dict(CONFIG['pesos'],conteudo=-1)}):
            c=copy.deepcopy(CONFIG);c.update(alteracao)
            with self.assertRaises(ValueError):validar_config(c)


class IntegracaoTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.raiz=Path(self.tmp.name)
        self.base=self.raiz/'base';shutil.copytree(ROOT/'organizador/exemplos/base',self.base)
        self.saida=self.raiz/'compilador'

    def tearDown(self):self.tmp.cleanup()

    def cli(self,args,seed='1'):
        p=subprocess.run([sys.executable,str(ROOT/'compilador/app.py'),'--base',str(self.base),'--saida',str(self.saida),*args],
                         capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONHASHSEED=seed))
        self.assertEqual(p.returncode,0,p.stderr)
        return json.loads(p.stdout)

    def test_cli_reprodutivel_consulta_e_base_intacta(self):
        antes={p.relative_to(self.base):p.read_bytes() for p in self.base.rglob('*') if p.is_file()}
        r=self.cli(['analisar'],seed='1');r2=self.cli(['analisar'],seed='98765')
        self.assertEqual(r['id'],r2['id'])
        self.assertEqual(len(list(self.saida.glob('*.json'))),2)
        self.assertEqual(self.cli(['consultar',r['id']])['id'],r['id'])
        self.assertEqual(antes,{p.relative_to(self.base):p.read_bytes() for p in self.base.rglob('*') if p.is_file()})
        path=Path(r['arquivo']);d=json.loads(path.read_text());d['estado']='alterado';path.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'corrompido'):app.consultar(self.saida,r['id'])

    def test_cli_par_e_similares(self):
        r=self.cli(['comparar','N32.a2.5.y.1','N32.a2.5.y.2'])
        self.assertEqual(r['par']['a'],'N32.a2.5.y.1')
        r=self.cli(['similares','N32.a2.5.y.1','--exaustivo'])
        self.assertEqual(r['candidatas_comparadas'],3)

    def test_exportacao_maior_que_uma_pagina_e_filtros(self):
        path=self.base/'dados/N32/a2/5/y.jsonl'
        with path.open('a',encoding='utf-8') as f:
            for n in range(101):f.write(json.dumps([0,f'Contrato de locação exemplo {n}.',[]])+'\n')
        snap=app.exportar(self.base,{'tema':'N32.a2.5.y'})
        self.assertEqual(len(snap['itens']),105)
        self.assertEqual(len({x['id'] for x in snap['itens']}),105)
        with self.assertRaises(ValueError):app.exportar(self.base,{'orgao':'inexistente'})

    def test_snapshot_bloqueia_base_em_publicacao(self):
        (self.base/'.transacao-pendente.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'interrompida'):app.exportar(self.base,{})

    def test_snapshot_nao_atravessa_escritor_ativo(self):
        (self.base/'.base.lock').write_text('escritor')
        with self.assertRaisesRegex(ValueError,'gravação'):app.exportar(self.base,{})

    def test_saida_na_base_e_recusada(self):
        with self.assertRaisesRegex(ValueError,'fora da base'):app.compilar(self.base,self.base/'compilador',CONFIG)


if __name__=='__main__':unittest.main()
