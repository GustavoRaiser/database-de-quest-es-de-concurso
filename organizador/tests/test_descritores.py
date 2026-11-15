import unittest
from basequestoes.descritores import descrever


class DescritoresTest(unittest.TestCase):
    def test_texto_assertivas_e_apoios_sem_ia(self):
        d=descrever({'enunciado':'Assinale a opção correta.', 'assertivas':['Sobre CONTRIBUICOES PREVIDENCIARIAS.'],
                     'textos_apoio':['Competência da Justiça do Trabalho.']})
        self.assertEqual(d['geracao'],'regras')
        self.assertIn('contribuicoes_previdenciarias',d['regras_aplicadas'])
        self.assertEqual({e['campo'] for e in d['evidencias']},{'assertiva','texto_apoio'})
        self.assertNotIn('modelo',d)

    def test_sem_correspondencia(self):
        d=descrever({'enunciado':'Qual é a cor da casa?', 'assertivas':['Azul','Verde']})
        self.assertEqual(d['conceitos'],['Não identificado'])
        self.assertTrue(d['pendencias'])

    def test_palavras_parciais_nao_disparam(self):
        d=descrever({'enunciado':'Discuta a comunidade.', 'assertivas':[]})
        self.assertEqual(d['regras_aplicadas'],[])


if __name__=='__main__':unittest.main()
