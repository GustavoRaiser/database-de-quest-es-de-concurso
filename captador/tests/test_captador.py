import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('captador_app', Path(__file__).resolve().parents[1]/'app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class CaptadorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.c = app.Captador(Path(self.tmp.name)/'trabalho')
        self.lote = self.c.criar({'prova':'ENAM fictício','edicao':'2026.1','caderno':'Tipo 1'})['id']

    def documento(self, tipo='prova', valor=b'%PDF-1.4\nprova ficticia'):
        return {'lote':self.lote,'nome':tipo+'.pdf','tipo':tipo,
                'situacao_gabarito':'definitivo' if tipo=='gabarito' else '',
                'conteudo_base64':base64.b64encode(valor).decode()}

    def test_lote_e_pendencias(self):
        m = self.c.ler(self.lote)
        self.assertEqual(m['estado'],'aguardando_prova')
        m = self.c.anexar(self.documento())
        self.assertEqual(m['estado'],'pronto_para_digitalizador')
        self.assertEqual(m['processamento'],'nao_iniciado')
        self.assertEqual(len(m['pendencias']),1)

    def test_gabaritos_vinculados_e_historico(self):
        prova = self.c.anexar(self.documento())['documentos'][0]
        d = self.documento('gabarito',b'gabarito preliminar')
        d['situacao_gabarito'] = 'preliminar'
        self.c.anexar(d)
        m = self.c.anexar(self.documento('gabarito',b'gabarito definitivo'))
        self.assertEqual(len(m['documentos']),3)
        self.assertFalse(m['pendencias'])
        for d in m['documentos'][1:]:
            self.assertEqual(d['referente_a'],prova['sha256'])
        self.assertEqual([d['situacao_gabarito'] for d in m['documentos'][1:]],['preliminar','definitivo'])

    def test_pasta_preserva_original_e_duplicata(self):
        p=self.c.raiz/'entrada/prova.pdf'
        p.write_bytes(b'original')
        d={'lote':self.lote,'nome':p.name,'entrada':p.name,'tipo':'prova'}
        self.assertEqual(self.c.estado()['entrada'][0]['nome'],p.name)
        self.c.anexar(d)
        self.assertEqual(p.read_bytes(),b'original')
        with self.assertRaises(ValueError): self.c.anexar(d)
        self.assertEqual(len(self.c.ler(self.lote)['documentos']),1)

    def test_recusa_gabarito_sem_prova(self):
        with self.assertRaises(ValueError): self.c.anexar(self.documento('gabarito'))

    def test_recusa_segunda_prova(self):
        self.c.anexar(self.documento())
        with self.assertRaises(ValueError): self.c.anexar(self.documento(valor=b'outra prova'))

    def test_integridade(self):
        m=self.c.anexar(self.documento())
        (self.c.pasta(self.lote)/m['documentos'][0]['arquivo']).write_bytes(b'alterado')
        with self.assertRaises(ValueError): self.c.ler(self.lote)
        self.assertEqual(len(self.c.estado()['erros']),1)

    def test_entrada_maliciosa_e_vazia(self):
        for campo, valor in [('nome','../prova.pdf'),('tipo','invalido'),('conteudo_base64',''),('conteudo_base64','@@@')]:
            d=self.documento();d[campo]=valor
            with self.subTest(campo=campo), self.assertRaises(ValueError): self.c.anexar(d)

    def test_symlink_entrada(self):
        p=Path(self.tmp.name)/'externo.pdf';p.write_bytes(b'segredo')
        (self.c.raiz/'entrada/link.pdf').symlink_to(p)
        self.assertEqual(self.c.estado()['entrada'],[])
        with self.assertRaises(ValueError):
            self.c.anexar({'lote':self.lote,'nome':'link.pdf','entrada':'link.pdf','tipo':'prova'})

    def test_identificacao_obrigatoria(self):
        with self.assertRaises(ValueError): self.c.criar({'prova':'ENAM'})


if __name__=='__main__': unittest.main()
