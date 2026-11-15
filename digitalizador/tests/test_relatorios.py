import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'digitalizador'))
spec=importlib.util.spec_from_file_location('adaptador_github',ROOT/'digitalizador/executar_github.py')
adaptador=importlib.util.module_from_spec(spec);spec.loader.exec_module(adaptador)

class RelatorioTest(unittest.TestCase):
    def test_pedido_invalido_substitui_sucesso_anterior_por_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);pedido=tmp/'pedido.json';relatorio=tmp/'relatorio.json'
            pedido.write_text('[]');relatorio.write_text('{"completo":true}')
            p=subprocess.run([sys.executable,str(ROOT/'digitalizador/pipeline.py'),'--pedido',str(pedido),
                              '--relatorio',str(relatorio)],capture_output=True,text=True)
            self.assertEqual(p.returncode,1)
            r=json.loads(relatorio.read_text())
            self.assertFalse(r['completo']);self.assertEqual(r['estado'],'falha')

    def test_adaptador_erro_inicial_nao_reutiliza_relatorio_antigo(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp);trabalho=raiz/'digitalizador/trabalho/github';(trabalho/'base').mkdir(parents=True)
            (trabalho/'relatorio.json').write_text('{"completo":true}')
            with patch.object(adaptador,'ROOT',raiz),patch.dict('os.environ',{'IDENTIFICACAO':'JSON quebrado'}):
                self.assertEqual(adaptador.main(),1)
            r=json.loads((trabalho/'relatorio.json').read_text())
            self.assertFalse(r['completo']);self.assertEqual(r['estado'],'falha')

class LocalGateTest(unittest.TestCase):
    def test_pipeline_bloqueia_local_antes_de_captacao(self):
        spec=importlib.util.spec_from_file_location('pipeline_gate',ROOT/'digitalizador/pipeline.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m,'cli',side_effect=AssertionError('Não deveria iniciar captação')):
                with self.assertRaisesRegex(ValueError,'habilitar_ia_local'):
                    m.executar({'analise_semantica':'local'},Path(tmp)/'cap',Path(tmp)/'dig',Path(tmp)/'base')
