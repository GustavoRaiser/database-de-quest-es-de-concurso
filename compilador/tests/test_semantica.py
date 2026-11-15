import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from semantica import MotorSemantico, validar_resposta, Ollama
from test_compilador import CONFIG,item,ROOT

SEM=json.loads((ROOT/'compilador/semantica.json').read_text())

class Backend:
    modelos={'embedding':{'nome':'teste','digest':'e1'},'avaliador':{'nome':'teste','digest':'a1'}}
    def embed(self,t):return [1,0] if 'contrato' in t.lower() else [0,1]
    def avaliar(self,a,b):
        return {'dimensoes':{k:{'score':80,'justificativa':'Estimativa de teste.',
                'trecho_a':a.splitlines()[0],'trecho_b':b.splitlines()[0]} for k in CONFIG['pesos']},'avisos':['Modelo de teste.']}

def gravar(path,obj):app.atomico(path,app.canon(obj).encode())

class SemanticaTest(unittest.TestCase):
    def test_cache_separacao_e_invalida_modelo(self):
        snapshot={'itens':[item(1,'Contrato válido.'),item(2,'Contrato regular.')]}
        with tempfile.TemporaryDirectory() as tmp:
            m=MotorSemantico(snapshot,CONFIG,SEM,Backend(),tmp,gravar);r=m.analisar(True)
            self.assertEqual(r['processamento_ia']['pares_ia_novos'],1)
            self.assertEqual(r['avaliacoes_ia'][0]['origem'],'novo')
            self.assertEqual(len(r['vetorizacoes_ia']),2)
            self.assertEqual(r['pares'][0]['estado'],'proposta_semantica_ia')
            self.assertIn('score_lexical',r['pares'][0])
            m2=MotorSemantico(snapshot,CONFIG,SEM,Backend(),tmp,gravar);r2=m2.analisar(True)
            self.assertEqual(r2['processamento_ia']['pares_ia_novos'],0)
            self.assertEqual(r2['processamento_ia']['pares_ia_cache'],1)
            outro=Backend();outro.modelos=copy.deepcopy(outro.modelos);outro.modelos['avaliador']['digest']='a2'
            r3=MotorSemantico(snapshot,CONFIG,SEM,outro,tmp,gravar).analisar(True)
            self.assertEqual(r3['processamento_ia']['pares_ia_novos'],1)

    def test_evidencia_inventada_nao_entra_em_grupo(self):
        b=Backend()
        def invalida(a,c):
            r=Backend().avaliar(a,c);r['dimensoes']['conteudo']['trecho_a']='inventado';return r
        b.avaliar=invalida
        with tempfile.TemporaryDirectory() as tmp:
            r=MotorSemantico({'itens':[item(1,'A contrato.'),item(2,'B contrato.')]},CONFIG,SEM,b,tmp,gravar).analisar(True)
            self.assertEqual(r['grupos'],[]);self.assertEqual(len(r['pendencias_ia']),1)
            self.assertEqual(list((Path(tmp)/'pares').glob('*.json')),[])

    def test_semantico_preserva_lexical_e_registra_execucao(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);base=tmp/'base';shutil.copytree(ROOT/'organizador/exemplos/base',base)
            out=tmp/'compilador'
            r=app.compilar_hibrido(base,out,CONFIG,SEM,backend=Backend())
            self.assertTrue(r['completo'])
            self.assertTrue((out/'ultimo.json').exists())
            self.assertTrue((out/'semantica/ultimo.json').exists())
            self.assertEqual(app.consultar(out,r['lexical']['id'])['estado'],'proposta_lexical')
            self.assertEqual(app.consultar(out/'semantica',r['semantica']['id'])['estado'],'proposta_semantica_ia')
            with patch('semantica.Ollama',side_effect=OSError('serviço ausente')):
                falha=app.compilar_hibrido(base,out,CONFIG,SEM)
            self.assertFalse(falha['completo']);self.assertEqual(falha['lexical']['estado'],'concluida')
            self.assertEqual(falha['semantica']['estado'],'falha')
            self.assertTrue(Path(falha['registro']).exists())

    def test_proibe_servico_externo(self):
        with self.assertRaises(ValueError):Ollama(dict(SEM,url='https://exemplo.com'))

    def test_textos_longos_nao_sao_cortados_para_avaliacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=MotorSemantico({'itens':[item(1,'contrato '*2600),item(2,'contrato')]},CONFIG,SEM,Backend(),tmp,gravar).analisar(True)
            self.assertEqual(len(r['pendencias_ia']),1)

if __name__=='__main__':unittest.main()
