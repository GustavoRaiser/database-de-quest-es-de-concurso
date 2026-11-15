import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('digitalizador_app', ROOT/'digitalizador/app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def pdf(paginas):
    objetos = [b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>', b'', b'<< /Type /Catalog /Pages 2 0 R >>']
    kids = []
    for linhas in paginas:
        comandos = []
        for x,y,texto in linhas:
            texto = texto.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            comandos.append(f'BT /F1 6 Tf 1 0 0 1 {x} {y} Tm ({texto}) Tj ET')
        stream = '\n'.join(comandos).encode('cp1252')
        cid = len(objetos)+1
        objetos.append(f'<< /Length {len(stream)} >>\nstream\n'.encode()+stream+b'\nendstream')
        pid = len(objetos)+1
        objetos.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 1 0 R >> >> /Contents {cid} 0 R >>'.encode())
        kids.append(f'{pid} 0 R')
    objetos[1] = f'<< /Type /Pages /Kids [{" ".join(kids)}] /Count {len(kids)} >>'.encode()
    saida = b'%PDF-1.4\n'; offsets=[]
    for i,obj in enumerate(objetos,1):
        offsets.append(len(saida));saida += f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    xref=len(saida);saida+=f'xref\n0 {len(objetos)+1}\n0000000000 65535 f \n'.encode()
    for n in offsets: saida+=f'{n:010d} 00000 n \n'.encode()
    return saida+f'trailer\n<< /Size {len(objetos)+1} /Root 3 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()


def documentos():
    paginas=[[(40,750,'ENAM - 2026.1 TIPO 1')], []]
    for inicio in (1,21,41,61):
        linhas=[(40,770,'DIREITO CIVIL')]
        for lado in range(2):
            y=755;x=40+lado*300
            for n in range(inicio+lado*10,inicio+lado*10+10):
                for linha in [str(n),'Assinale a alternativa sobre contrato.']+[f'({c}) Opcao {c}.' for c in 'ABCDE']:
                    linhas.append((x,y,linha));y-=7
        paginas.append(linhas)
    gab=[(30,800,'ENAM - Exame Nacional da Magistratura - Prova Tipo 1 - Turno: Tarde')]
    for n in range(1,81):
        x=30+((n-1)//20)*140
        y=780-((n-1)%20)*22
        gab.extend([(x,y,str(n)),(x,y-9,'*' if n==42 else 'B')])
    gab.append((30,100,'* Questão Anulada'))
    return pdf(paginas), pdf([gab])


class ExtratorTest(unittest.TestCase):
    def test_pdf_sem_texto_e_edicao_errada(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p.pdf';g=Path(tmp)/'g.pdf'
            raw,gab=documentos();p.write_bytes(raw);g.write_bytes(gab)
            with self.assertRaisesRegex(ValueError,'Edição'):app.extrair(p,g,'2025.1')
            p.write_bytes(pdf([[(40,750,'ENAM - 2026.1 TIPO 1')],[],[]]))
            with self.assertRaisesRegex(ValueError,'OCR'):app.extrair(p,g,'2026.1')

    def test_segmentacao_e_continuidade(self):
        blocos=[{'pagina':3,'texto':'DIREITO CIVIL\n1\nAssinale sobre contrato.\n(A) A\n(B) B'},
                {'pagina':4,'texto':'(C) C\n(D) D\n(E) E'}]
        qs=app.separar(blocos,1)
        self.assertEqual(qs[0]['paginas'],[3,4])
        self.assertEqual(qs[0]['assertivas'],list('ABCDE'))

    def test_recusa_incompletos(self):
        for texto in ('1\nx\n(A) A', '2\nx\n(A) A\n(B) B\n(C) C\n(D) D\n(E) E'):
            with self.assertRaises(ValueError):app.separar([{'pagina':3,'texto':texto}],1)

    def test_gabarito_tipo_nao_mistura(self):
        t='ENAM - Exame Nacional da Magistratura - Prova Tipo 1\n1\nB\nENAM - Exame Nacional da Magistratura - Prova Tipo 2\n1\nC\n'
        self.assertEqual(app.respostas_tipo1(t,1),{'1':'B'})
        with self.assertRaises(ValueError): app.respostas_tipo1(t.replace('1\nB','1\n*'),1)

    def test_fluxo_completo_com_pdfs_sinteticos(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp)/'captador';saida=Path(tmp)/'resultados'
            def cap(cmd,dados):
                p=subprocess.run([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(raiz),cmd],input=json.dumps(dados),text=True,capture_output=True)
                self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
            m=cap('criar',{'prova':'ENAM teste','edicao':'2026.1','caderno':'Tipo 1','orgao_id':'0','cargo_id':'0',
                          'orgao':'Ficticio','cargo':'Ficticio','banca':'FGV','ano':'2026'})
            for tipo,raw in zip(('prova','gabarito'),documentos()):
                (raiz/'entrada'/f'{tipo}.pdf').write_bytes(raw)
                d={'lote':m['id'],'tipo':tipo,'nome':tipo+'.pdf','entrada':tipo+'.pdf'}
                if tipo=='gabarito':d['situacao_gabarito']='definitivo'
                m=cap('anexar',d)
            cap('encaminhar',{'lote':m['id'],'gabarito_sha256':m['documentos'][1]['sha256']})
            r=app.processar(raiz,m['id'],saida,ROOT/'organizador')
            self.assertEqual(r['contagens'],{'questoes':80,'assertivas':400,'anuladas':['42']})
            self.assertTrue(all(q['abordagem']['geracao']=='regras' for q in r['questoes']))
            self.assertEqual(cap('estado',None)['lotes'][0]['processamento'],'extraido_com_pendencias')
            self.assertEqual(len(list(saida.glob('*.json'))),1)
            # Invalida o pacote atual; o extrator deve recusar, mesmo com resultado antigo.
            (raiz/'entrada/anexo.txt').write_text('Retificacao')
            cap('anexar',{'lote':m['id'],'tipo':'complemento','nome':'anexo.txt','entrada':'anexo.txt'})
            with self.assertRaises(ValueError):app.processar(raiz,m['id'],saida,ROOT/'organizador')


if __name__=='__main__':unittest.main()
