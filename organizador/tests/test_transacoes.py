import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from basequestoes.core import Base, Erro, atomico, ler_json, serializar
from basequestoes import transacoes
from basequestoes.incorporacao import reservar

ROOT = Path(__file__).resolve().parents[1]


class TransacoesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        for nome in ('manifesto.json','catalogos.json','indice.json'):
            shutil.copyfile(ROOT/nome,self.base/nome)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reserva_estavel_e_conflito(self):
        r=reservar(self.base,{'orgao':'Fictício','cargo':'Cargo'})
        self.assertEqual(r,{'orgao_id':'0','cargo_id':'0'})
        self.assertEqual(reservar(self.base,{'orgao':'Fictício','cargo':'Cargo'}),r)
        with self.assertRaises(Erro):reservar(self.base,{'orgao':'Outro','cargo':'Cargo','orgao_id':'0'})
        Base(self.base).validar()

    def test_estado_parcial_bloqueia_leitura_e_recupera(self):
        aplicar=transacoes.aplicar
        def interromper(raiz,plano):
            item=plano['arquivos'][0]
            atomico(raiz/item['caminho'],(raiz/'.transacoes'/plano['id']/'novos'/item['caminho']).read_bytes())
            raise OSError('interrupção simulada')
        with patch.object(transacoes,'aplicar',interromper):
            with self.assertRaises(OSError):reservar(self.base,{'orgao':'Teste','cargo':'Teste'})
        with self.assertRaisesRegex(Erro,'interrompida'):Base(self.base)
        self.assertTrue(transacoes.recuperar(self.base)['recuperada'])
        self.assertFalse(transacoes.recuperar(self.base)['recuperada'])
        self.assertEqual(Base(self.base).catalogos['cargos'],{'0.0':'Teste'})

    def test_leitor_antigo_recusa_revisao_nova(self):
        leitor=Base(self.base)
        reservar(self.base,{'orgao':'Teste','cargo':'Teste'})
        with self.assertRaisesRegex(Erro,'mudou'):leitor.conferir_leitura()

    def test_falha_validacao_nao_altera_base(self):
        antes=(self.base/'catalogos.json').read_bytes()
        def invalido(base):
            atomico(base.local('catalogos.json'),serializar({'orgaos':{}}).encode())
        with self.assertRaises(Erro):transacoes.executar(self.base,invalido)
        self.assertEqual(antes,(self.base/'catalogos.json').read_bytes())
        Base(self.base).validar()


if __name__=='__main__':unittest.main()
