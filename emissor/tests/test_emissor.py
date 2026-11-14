import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("servidor", ROOT / "emissor/servidor.py")
servidor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(servidor)


class EmissorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name) / "base"
        shutil.copytree(ROOT / "organizador/exemplos/base", cls.base)
        c = json.loads((cls.base / "catalogos.json").read_text())
        c['orgaos']['X'] = 'Outro órgão'
        c['cargos']['X.a2'] = 'Mesmo código local de cargo'
        c['disciplinas']['X.a2.5'] = 'Outra disciplina'
        c['temas']['X.a2.5.y'] = 'Outro tema'
        (cls.base / 'catalogos.json').write_text(json.dumps(c))
        indice = json.loads((cls.base / 'indice.json').read_text())
        indice['temas']['X.a2.5.y'] = 'dados/X/a2/5/y.jsonl'
        (cls.base / 'indice.json').write_text(json.dumps(indice))
        q = cls.base / 'dados/X/a2/5/y.jsonl'
        q.parent.mkdir(parents=True)
        q.write_text('[0,"Outra questão",["A","B"]]\n')
        cls.antes = cls.hashes()
        cls.server = servidor.criar_servidor(cls.base, 0, Path(cls.temp.name)/'captacoes')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def hashes(cls):
        return {str(p.relative_to(cls.base)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in cls.base.rglob('*') if p.is_file()}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        assert cls.hashes() == cls.antes, 'Emissor alterou a base'
        cls.temp.cleanup()

    def get(self, query=''):
        with urlopen(self.url + '/api/questoes' + query) as r:
            return json.load(r)

    def test_sem_filtro_toda_base(self):
        d = self.get()
        self.assertEqual(d['total'], 5)
        self.assertEqual(len(d['itens']), 5)
        self.assertIsNotNone(d['itens'][0]['metadados'])

    def test_cada_filtro_independente(self):
        for query in ('orgao=N32', 'cargo=N32.a2', 'disciplina=N32.a2.5', 'tema=N32.a2.5.y'):
            with self.subTest(query=query):
                self.assertEqual(self.get('?' + query)['total'], 4)

    def test_combinacao_e_codigos_locais(self):
        self.assertEqual(self.get('?orgao=X&tema=N32.a2.5.y')['total'], 0)
        self.assertEqual(self.get('?orgao=X&cargo=X.a2')['total'], 1)
        self.assertEqual(self.get('?cargo=X.a2')['itens'][0]['id'], 'X.a2.5.y.1')

    def test_paginacao_sem_perdas(self):
        ids = []
        for n in range(1, 4):
            d = self.get(f'?pagina={n}&por_pagina=2')
            self.assertEqual(d['paginas'], 3)
            ids.extend(q['id'] for q in d['itens'])
        self.assertEqual(len(ids), 5)
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(self.get('?pagina=99')['itens'], [])

    def test_parametros_invalidos(self):
        for q in ('?pagina=0', '?por_pagina=101', '?orgao=nao-existe', '?cargo=a2', '?pagina=x', '?x=y', '?pagina=1&pagina=2'):
            with self.subTest(q=q), self.assertRaises(HTTPError) as e:
                self.get(q)
            self.assertEqual(e.exception.code, 400)

    def test_interface_e_catalogos(self):
        for path in ('/', '/app.js', '/style.css', '/api/catalogos'):
            with urlopen(self.url + path) as r:
                self.assertEqual(r.status, 200)
                self.assertTrue(r.read())
                self.assertIn("object-src 'none'", r.headers['Content-Security-Policy'])

    def test_recursos_e_travessia(self):
        meta = self.get()['itens'][0]['metadados']
        recurso = meta['recursos'][0]
        with urlopen(self.url + '/' + recurso['arquivo']) as r:
            self.assertEqual(hashlib.sha256(r.read()).hexdigest(), recurso['sha256'])
            self.assertEqual(r.headers['Content-Disposition'], 'attachment')
        with self.assertRaises(HTTPError):
            urlopen(self.url + '/recursos/../../manifesto.json')

    def test_base_vazia(self):
        d = servidor.consultar(ROOT/'organizador', 'emitir')
        self.assertEqual((d['total'], d['itens']), (0, []))

    def test_captacao_integrada_e_protecao(self):
        with urlopen(self.url+'/api/captacao') as r:
            estado=json.load(r)
        dados=json.dumps({'prova':'ENAM teste','edicao':'2026.1','caderno':'Tipo 1','orgao_id':'N32','cargo_id':'a2','orgao':'Órgão fictício','cargo':'Cargo fictício','banca':'FGV','ano':'2026'}).encode()
        url=self.url+'/api/captacao/criar'
        with self.assertRaises(HTTPError) as erro:
            urlopen(Request(url,data=dados,headers={'Content-Type':'application/json'}))
        self.assertEqual(erro.exception.code,403)
        headers={'Content-Type':'application/json','Origin':self.url,'X-Captacao-Token':estado['token_captacao']}
        with urlopen(Request(url,data=dados,headers=headers)) as r:
            lote=json.load(r)
        import base64
        dados=json.dumps({'lote':lote['id'],'nome':'prova.pdf','tipo':'prova',
                          'conteudo_base64':base64.b64encode(b'%PDF-1.4\nfixture').decode()}).encode()
        with urlopen(Request(self.url+'/api/captacao/anexar',data=dados,headers=headers)) as r:
            self.assertEqual(json.load(r)['estado'],'aguardando_gabarito')
        args=json.dumps({'lote':lote['id']}).encode()
        with self.assertRaises(HTTPError) as erro:
            urlopen(Request(self.url+'/api/captacao/encaminhar',data=args,headers=headers))
        self.assertEqual(erro.exception.code,400)
        self.assertEqual(self.get()['total'],5)
        with urlopen(self.url+'/captacao.js') as r:
            self.assertEqual(r.status,200)


if __name__ == '__main__':
    unittest.main()
