import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import Captador
import recepcao


class RecepcaoTest(unittest.TestCase):
    def test_qconcursos_baixa_todos_pares_da_pagina_e_retoma(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Captador(tmp)
            candidatos=[{'titulo':'ENAM 2026.1','prova_url':'https://exemplo.org/1.pdf','gabarito_url':'https://exemplo.org/g1.pdf'},
                        {'titulo':'Outra prova','prova_url':'https://exemplo.org/2.pdf','gabarito_url':''}]
            def obter(url):return b'%PDF-1.4\n'+url.encode(),{'url_final':url,'content_type':'application/pdf','redirecionamentos':[]}
            with patch.object(recepcao,'descobrir',return_value={'pdf_direto':False,'candidatos':candidatos}),patch.object(recepcao,'obter',side_effect=obter) as download:
                r=recepcao.receber(c,{'urls':['https://www.qconcursos.com/provas']})
                self.assertEqual([v['estado'] for v in r['reservas']],['par_reservado','aguardando_par'])
                self.assertEqual(download.call_count,3)
                recepcao.receber(c,{'urls':['https://www.qconcursos.com/provas']})
                self.assertEqual(download.call_count,3)
                self.assertEqual(len(list((Path(tmp)/'reservados').glob('*/conteudo_*.pdf'))),3)

    def test_duas_urls_diretas_qconcursos_formam_par(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Captador(tmp)
            urls=['https://arquivos.qconcursos.com/prova/arquivo_prova/123/enam-2026-1-prova.pdf',
                  'https://arquivos.qconcursos.com/prova/arquivo_gabarito/123/enam-2026-1-gabarito.pdf']
            with patch.object(recepcao,'obter',side_effect=lambda u:(b'%PDF-1.4 '+u.encode(),{})):
                r=recepcao.receber(c,{'urls':urls})
            self.assertEqual(len(r['reservas']),1)
            self.assertEqual(r['reservas'][0]['estado'],'par_reservado')
            self.assertEqual(len(c.estado()['reservas']),1)

    def test_nome_nao_declara_gabarito_definitivo(self):
        self.assertEqual(recepcao.identidade('enam-2026.1')['edicao'],'2026.1')
        self.assertEqual(recepcao.identidade('qualquer prova'),{})
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);entrada=tmp/'entrada';entrada.mkdir();c=Captador(tmp/'captador')
            for sufixo in ('cad','gab'):(entrada/f'enam-2026.1_{sufixo}.pdf').write_bytes(b'%PDF-1.4 '+sufixo.encode())
            r=recepcao.receber(c,{'pasta':str(entrada)})['reservas'][0]
            i=dict(r['identificacao_sugerida'],orgao_id='0',cargo_id='0')
            with self.assertRaisesRegex(ValueError,'situacao_gabarito'):recepcao.preparar(c,{'reserva':r['id'],'identificacao':i})
            self.assertEqual(c.estado()['lotes'],[])

    def test_download_incompleto_permanece_reservado(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Captador(tmp)
            with patch.object(recepcao,'obter',side_effect=[(b'%PDF-1.4 prova',{}),OSError('indisponível')]):
                r=recepcao.receber(c,{'prova_url':'https://exemplo.org/p.pdf','gabarito_url':'https://exemplo.org/g.pdf'})['reservas'][0]
            self.assertEqual(r['estado'],'aguardando_par')
            self.assertIn('gabarito',r['erros'])
            self.assertEqual(c.estado()['lotes'],[])



class RecepcaoRegressaoTest(unittest.TestCase):
    def test_reserva_corrompida_nao_interrompe_outros_pares(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Captador(tmp)
            candidatos=[{'titulo':f'Prova {n}','prova_url':f'https://exemplo.org/{n}_cad.pdf',
                         'gabarito_url':f'https://exemplo.org/{n}_gab.pdf'} for n in (1,2)]
            def obter(url):return b'%PDF-1.4 '+url.encode(),{}
            with patch.object(recepcao,'descobrir',return_value={'pdf_direto':False,'candidatos':candidatos}),patch.object(recepcao,'obter',side_effect=obter):
                primeiro=recepcao.receber(c,{'urls':['https://exemplo.org/provas']})
                r=primeiro['reservas'][0]
                (Path(tmp)/'reservados'/r['id']/r['documentos']['prova']['arquivo']).write_bytes(b'corrompido')
                segundo=recepcao.receber(c,{'urls':['https://exemplo.org/provas']})
            self.assertEqual(len(segundo['erros']),1)
            self.assertEqual(len(segundo['reservas']),1)
            self.assertEqual(segundo['reservas'][0]['titulo'],'Prova 2')

    def test_urls_repetidas_nao_repetem_reserva_no_resultado(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Captador(tmp)
            candidato={'titulo':'Prova','prova_url':'https://exemplo.org/p.pdf','gabarito_url':'https://exemplo.org/g.pdf'}
            with patch.object(recepcao,'descobrir',return_value={'pdf_direto':False,'candidatos':[candidato]}),patch.object(recepcao,'obter',return_value=(b'%PDF-1.4',{})):
                r=recepcao.receber(c,{'urls':['https://exemplo.org/pagina']*2})
            self.assertEqual(len(r['reservas']),1)

if __name__=='__main__':unittest.main()
