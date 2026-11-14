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
        self.lote = self.c.criar({'prova':'ENAM fictício','edicao':'2026.1','caderno':'Tipo 1','orgao_id':'N32','cargo_id':'a2','orgao':'Órgão de teste','cargo':'Cargo de teste','banca':'FGV','ano':'2026'})['id']

    def documento(self, tipo='prova', valor=b'%PDF-1.4\nprova ficticia'):
        return {'lote':self.lote,'nome':tipo+'.pdf','tipo':tipo,
                'situacao_gabarito':'definitivo' if tipo=='gabarito' else '',
                'conteudo_base64':base64.b64encode(valor).decode()}

    def test_lote_e_pendencias(self):
        m = self.c.ler(self.lote)
        self.assertEqual(m['estado'],'aguardando_prova')
        m = self.c.anexar(self.documento())
        self.assertEqual(m['estado'],'aguardando_gabarito')
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


    def test_protocolo_estavel_e_duplicata_de_identidade(self):
        m=self.c.ler(self.lote)
        self.assertEqual(m['protocolo'],'N32.a2.0')
        with self.assertRaises(ValueError): self.c.criar(m['identificacao'])
        outro=dict(m['identificacao'],caderno='Tipo 2')
        self.assertEqual(self.c.criar(outro)['protocolo'],'N32.a2.1')
        conflito=dict(outro,caderno='Tipo 3',orgao='Outro nome')
        with self.assertRaises(ValueError): self.c.criar(conflito)

    def test_bloqueio_e_encaminhamento_idempotente(self):
        with self.assertRaises(ValueError): self.c.encaminhar({'lote':self.lote})
        self.c.anexar(self.documento())
        with self.assertRaises(ValueError): self.c.encaminhar({'lote':self.lote})
        m=self.c.anexar(self.documento('gabarito',b'respostas'))
        self.assertTrue(m['liberado'])
        self.assertEqual(m['estado'],'pronto_para_digitalizador')
        args={'lote':self.lote,'gabarito_sha256':m['documentos'][1]['sha256']}
        d=self.c.encaminhar(args)
        self.assertEqual(self.c.encaminhar(args),d)
        self.assertEqual(len(list((self.c.raiz/'encaminhamentos').glob('*.json'))),1)
        self.assertEqual(len([h for h in self.c.ler(self.lote)['historico'] if h['evento']=='encaminhado']),1)
        self.c.registrar_analise({'lote':self.lote,'encaminhamento':d['id'],'resultado':'concluida','relatorio':'Conferência manual de teste'})
        self.assertEqual(self.c.ler(self.lote)['analise']['declarada_por'],'usuario')
        self.c.anexar(self.documento('complemento',b'anexo novo'))
        self.assertNotIn('analise',self.c.ler(self.lote))

    def test_gabarito_falso_e_original_corrompido_nao_passam(self):
        self.c.anexar(self.documento())
        m=self.c.anexar(self.documento('gabarito',b'respostas'))
        args={'lote':self.lote,'gabarito_sha256':'0'*64}
        with self.assertRaises(ValueError): self.c.encaminhar(args)
        args['gabarito_sha256']=m['documentos'][1]['sha256']
        path=self.c.pasta(self.lote)/'lote.json'
        raw=json.loads(path.read_text())
        raw['documentos'][1]['referente_a']='f'*64
        path.write_text(json.dumps(raw))
        with self.assertRaises(ValueError): self.c.encaminhar(args)
        self.assertEqual(list((self.c.raiz/'encaminhamentos').glob('*.json')),[])

    def test_lote_antigo_bloqueado_ate_identificacao(self):
        path=self.c.pasta(self.lote)/'lote.json'
        m=json.loads(path.read_text());i=m['identificacao'];m['versao']=1
        m.pop('protocolo');m.pop('grupo');path.write_text(json.dumps(m))
        self.c.anexar(self.documento())
        self.c.anexar(self.documento('gabarito',b'respostas'))
        self.assertFalse(self.c.ler(self.lote)['liberado'])
        with self.assertRaises(ValueError): self.c.encaminhar({'lote':self.lote})
        d=self.c.identificar(dict(i,lote=self.lote))
        self.assertTrue(d['liberado'])
        self.assertEqual(d['protocolo'],'N32.a2.0')

    def test_filtros_e_codigos_invalidos(self):
        m=self.c.ler(self.lote)
        for campo,valor in [('ano','xx'),('orgao_id','../x'),('cargo_id','01'),('data_aplicacao','2026-02-30'),('uf','ZZ')]:
            with self.subTest(campo=campo),self.assertRaises(ValueError):
                self.c.criar(dict(m['identificacao'],caderno='Outro',**{campo:valor}))

    def test_original_ausente_ou_corrompido_bloqueia_fila(self):
        self.c.anexar(self.documento())
        m=self.c.anexar(self.documento('gabarito',b'respostas'))
        args={'lote':self.lote,'gabarito_sha256':m['documentos'][1]['sha256']}
        p=self.c.pasta(self.lote)/m['documentos'][0]['arquivo']
        p.write_bytes(b'prova adulterada')
        with self.assertRaises(ValueError): self.c.encaminhar(args)
        p.unlink()
        with self.assertRaises(ValueError): self.c.encaminhar(args)
        self.assertEqual(list((self.c.raiz/'encaminhamentos').glob('*.json')),[])

if __name__=='__main__': unittest.main()

