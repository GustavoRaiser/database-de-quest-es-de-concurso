import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from basequestoes.core import Base, Erro
from basequestoes.abordagem import preparar, registrar, validar

MODULO = Path(__file__).resolve().parents[1]


class AbordagemTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)/'base'
        shutil.copytree(MODULO/'exemplos/base', self.raiz)
        self.base = Base(self.raiz)
        self.id = 'N32.a2.5.y.1'
        self.path = self.raiz/'dados/N32/a2/5/y.jsonl'
        self.original = self.path.read_bytes()

    def perfil(self):
        tarefa = preparar(self.base, self.id)
        p = copy.deepcopy(tarefa['formato_resposta'])
        p.update(geracao='humano', autor='teste', sintese='Perfil fictício para testar o contrato',
                 evidencias=[{'campo':'assertiva','indice':2,'trecho':'Segunda assertiva.'}])
        return p

    def test_preparacao_inclui_todo_conteudo(self):
        m = preparar(self.base, self.id)
        self.assertEqual(len(m['entrada']['assertivas']), 2)
        self.assertEqual(len(m['entrada']['recursos']), 2)
        self.assertEqual(m['classificacao']['tema'], 'Tema de exemplo')
        self.assertEqual(len(m['base_sha256']), 64)

    def test_registro_e_substituicao_preservam_dados(self):
        perfil = self.perfil()
        registrar(self.base, 'N32.a2.5.y', {'1':perfil})
        self.assertEqual(self.base.consultar(self.id)['metadados']['abordagem']['sintese'], perfil['sintese'])
        self.assertEqual(self.path.read_bytes(), self.original)
        with self.assertRaises(Erro): registrar(self.base, 'N32.a2.5.y', {'1':perfil})
        perfil['sintese'] = 'Outra descrição fictícia'
        registrar(self.base, 'N32.a2.5.y', {'1':perfil}, substituir=True)
        m = self.base.metadados('N32.a2.5.y')['1']
        self.assertEqual(len(m['historico_abordagens']), 1)
        self.assertIn('origens', m)
        self.assertIn('gabarito', m)
        self.assertEqual(self.base.validar()['questoes'], 4)

    def test_evidencia_e_hash_invalidos(self):
        for campo, valor in [('base_sha256','0'*64), ('evidencias',[]), ('conceitos',['a','A']),
                             ('raciocinio','nao_existe'), ('versao_criterio',True)]:
            p=self.perfil();p[campo]=valor
            with self.subTest(campo=campo), self.assertRaises(Erro):
                registrar(self.base,'N32.a2.5.y',{'1':p})
        p=self.perfil();p['evidencias'][0]['trecho']='Trecho inexistente'
        with self.assertRaises(Erro): registrar(self.base,'N32.a2.5.y',{'1':p})
        p=self.perfil();p['evidencias'][0]['indice']=0
        with self.assertRaises(Erro): registrar(self.base,'N32.a2.5.y',{'1':p})

    def test_modelo_obrigatorio_para_ia(self):
        p=self.perfil();p['geracao']='ia';p.pop('modelo')
        with self.assertRaises(Erro): registrar(self.base,'N32.a2.5.y',{'1':p})

    def test_alteracao_situacao_nao_invalida_perfil(self):
        registrar(self.base,'N32.a2.5.y',{'1':self.perfil()})
        dados=self.path.read_text().splitlines();q=json.loads(dados[0]);q[0]=1;dados[0]=json.dumps(q)
        self.path.write_text('\n'.join(dados)+'\n')
        self.base.validar()
        q[1]+=' Texto alterado';dados[0]=json.dumps(q);self.path.write_text('\n'.join(dados)+'\n')
        with self.assertRaises(Erro): self.base.validar()

    def test_lote_atomico_e_origem_obrigatoria(self):
        meta=self.raiz/'dados/N32/a2/5/y_md.json';antes=meta.read_bytes()
        with self.assertRaises(Erro): registrar(self.base,'N32.a2.5.y',{'1':self.perfil(),'2':self.perfil()})
        self.assertEqual(meta.read_bytes(),antes)
        self.assertFalse((self.raiz/'.base.lock').exists())

    def test_cli_harness_completa(self):
        def cmd(*args):
            return json.loads(subprocess.check_output([sys.executable,'-m','basequestoes','--base',str(self.raiz),*args],cwd=MODULO))
        tarefa=cmd('preparar-abordagem',self.id)
        self.assertEqual(tarefa['id'], self.id)
        resposta=Path(self.tmp.name)/'resposta.json'
        resposta.write_text(json.dumps({'1':self.perfil()}))
        self.assertEqual(cmd('registrar-abordagens','N32.a2.5.y',str(resposta))['registradas'],1)
        self.assertIn('abordagem',cmd('emitir')['itens'][0]['metadados'])


if __name__=='__main__': unittest.main()
