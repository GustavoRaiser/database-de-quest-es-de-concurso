import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from basequestoes.core import Base, Erro, decodificar, linhas, serializar


EXEMPLO = Path(__file__).resolve().parents[1] / "exemplos/base"


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name) / "base"
        shutil.copytree(EXEMPLO, self.raiz)
        self.base = Base(self.raiz)
        self.dados = self.raiz / "dados/N32/a2/5/y.jsonl"
        self.original = self.dados.read_bytes()

    def metadata(self, n=2):
        return {"questao": n, "origens": [{"fonte": "teste", "id_externo": "abc", "coletado_em": "2026-11-14"}]}

    def mapa(self, *numeros):
        return {str(n): {k: v for k, v in self.metadata(n).items() if k != "questao"} for n in numeros}

    def entrada_lote(self):
        m = json.loads((self.raiz / "importacoes/exemplo-ficticio/manifesto.json").read_text())
        r = json.loads((self.raiz / "importacoes/exemplo-ficticio/relatorio.json").read_text())
        return m, r

    def test_validar_exemplo_e_consulta(self):
        self.assertEqual(self.base.validar(), {"temas": 1, "questoes": 4, "metadados": 1, "lotes": 1})
        q = self.base.consultar("N32.a2.5.y.1")
        self.assertEqual(q["questao"][1], "Enunciado fictício da primeira questão.")
        self.assertNotIn("questao", q["metadados"])
        self.assertEqual(q["metadados"]["origens"][0]["numero_original"], "41")
        self.assertIsNone(self.base.consultar("N32.a2.5.y.2")["metadados"])
        self.assertIn("\n", self.base.questao("N32.a2.5.y.4")[1])

    def test_linha_decimal_10(self):
        with self.dados.open("ab") as f:
            for i in range(5, 11):
                f.write(serializar([0, f"Questão {i}", []]).encode())
        self.assertEqual(self.base.questao("N32.a2.5.y.10")[1], "Questão 10")

    def test_ids_invalidos(self):
        for id_ in ("N32.a2.5.y.0", "N32.a2.5.y.01", "N32.a2.5.y.-1", "N32.a2.5.y.A", "N32.a2.5.y.5", "../../x"):
            with self.subTest(id=id_), self.assertRaises(Erro):
                self.base.questao(id_)

    def test_gravar_metadados_nao_muda_questoes(self):
        self.base.registrar_metadados("N32.a2.5.y", self.mapa(2))
        self.assertEqual(self.dados.read_bytes(), self.original)
        self.assertEqual(self.base.validar()["metadados"], 2)

    def test_mapa_esparso_independente_da_ordem(self):
        self.base.registrar_metadados("N32.a2.5.y", self.mapa(4, 2))
        self.assertEqual(self.base.consultar("N32.a2.5.y.4")["metadados"]["origens"][0]["id_externo"], "abc")
        self.assertIsNone(self.base.consultar("N32.a2.5.y.3")["metadados"])
        path = self.dados.with_name("y_md.json")
        mapa = json.loads(path.read_text())
        self.assertEqual(set(mapa), {"1", "2", "4"})
        self.assertNotIn("questao", mapa["4"])
        self.assertEqual(self.dados.read_bytes(), self.original)

    def test_arquivo_ausente_e_mapa_vazio(self):
        path = self.dados.with_name("y_md.json")
        path.unlink()
        self.assertIsNone(self.base.consultar("N32.a2.5.y.1")["metadados"])
        self.base.registrar_metadados("N32.a2.5.y", self.mapa(2))
        self.assertEqual(set(json.loads(path.read_text())), {"2"})
        path.write_text('{}\n', encoding="utf-8")
        self.assertIsNone(self.base.consultar("N32.a2.5.y.2")["metadados"])

    def test_formato_mapa_invalido(self):
        for mapa in ([], {"0": {}}, {"01": {}}, {"A": {}}, {"2": []}, {"2": self.metadata(2)}):
            with self.subTest(mapa=mapa), self.assertRaises(Erro):
                self.base.validar_mapa_metadados("N32.a2.5.y", mapa)

    def test_detecta_restos_do_formato_antigo(self):
        path = self.raiz / "metadados/N32/a2/5/y.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(serializar(self.metadata(2)), encoding="utf-8")
        with self.assertRaises(Erro):
            self.base.validar()

    def test_validacao_lote_metadados_antes_de_escrever(self):
        meta = self.raiz / "dados/N32/a2/5/y_md.json"
        antes = meta.read_bytes()
        with self.assertRaises(Erro):
            self.base.registrar_metadados("N32.a2.5.y", self.mapa(2, 999))
        self.assertEqual(meta.read_bytes(), antes)
        self.assertFalse((self.raiz / ".base.lock").exists())

    def test_nao_sobrescreve_metadados(self):
        with self.assertRaises(Erro):
            self.base.registrar_metadados("N32.a2.5.y", self.mapa(1))

    def test_gabarito_posicoes_e_rotulos_independentes(self):
        m = self.metadata()
        m["gabarito"] = {"situacao": "definitivo", "alternativas_corretas": [2], "rotulos_originais": ["C"]}
        self.base.metadado("N32.a2.5.y", m)
        for respostas in ([0], [4], [True], [1, 1], []):
            m["gabarito"]["alternativas_corretas"] = respostas
            with self.subTest(respostas=respostas), self.assertRaises(Erro):
                self.base.metadado("N32.a2.5.y", m)

    def test_gabarito_ausente_e_anulado(self):
        m = self.metadata(3)
        m["gabarito"] = {"situacao": "anulado", "alternativas_corretas": []}
        self.base.metadado("N32.a2.5.y", m)
        m["questao"] = 2
        with self.assertRaises(Erro):
            self.base.metadado("N32.a2.5.y", m)
        m["gabarito"]["situacao"] = "ausente"
        self.base.metadado("N32.a2.5.y", m)

    def test_recurso_deduplica_por_bytes(self):
        p = Path(self.temp.name) / "html.txt"
        p.write_text('<p>Texto com <strong>ênfase</strong>.</p>', encoding="utf-8")
        a = self.base.guardar_recurso(p, "text/html")
        b = self.base.guardar_recurso(p, "text/html")
        self.assertEqual(a, b)
        self.assertEqual(self.base.local(a["arquivo"]).read_bytes(), p.read_bytes())
        self.assertEqual(a["sha256"], hashlib.sha256(p.read_bytes()).hexdigest())
        self.assertEqual(self.dados.read_bytes(), self.original)

    def test_recurso_corrompido_ou_ausente(self):
        m = self.base.metadados("N32.a2.5.y")["1"]
        caminho = self.base.local(m["recursos"][0]["arquivo"])
        caminho.write_bytes(b"alterado")
        with self.assertRaises(Erro):
            self.base.validar()
        caminho.unlink()
        with self.assertRaises((Erro, OSError)):
            self.base.validar()

    def test_destino_assertiva_e_texto_apoio(self):
        m = copy.deepcopy(self.base.metadados("N32.a2.5.y")["1"])
        m["questao"] = 1
        recurso = m["recursos"][0]
        recurso.update(posicao="assertiva", indice=3)
        with self.assertRaises(Erro):
            self.base.metadado("N32.a2.5.y", m)
        recurso["indice"] = 2
        self.base.metadado("N32.a2.5.y", m)
        recurso.update(posicao="texto_apoio", indice=1)
        with self.assertRaises(Erro):
            self.base.metadado("N32.a2.5.y", m)
        m["textos_apoio"] = ["Texto preservado."]
        self.base.metadado("N32.a2.5.y", m)

    def test_lote_duplicado_outro_nome(self):
        m, r = self.entrada_lote()
        m["id"] = "outro-nome"
        with self.assertRaises(Erro):
            self.base.registrar_lote(m, r)
        self.assertFalse((self.raiz / "importacoes/outro-nome").exists())

    def test_novo_lote_e_mapeamento(self):
        m, r = self.entrada_lote()
        m["id"] = "outro-lote"
        r["mapeamento"] = [{"numero_original": "2", "questao_id": "N32.a2.5.y.2"}]
        self.base.registrar_lote(m, r)
        self.assertEqual(self.base.validar()["lotes"], 2)
        self.assertEqual(self.dados.read_bytes(), self.original)

    def test_pendencias_e_destinos_invalidos(self):
        m, r = self.entrada_lote()
        r["pendencias"] = ["figura ausente"]
        with self.assertRaises(Erro):
            self.base.lote(m, r)
        r["pendencias"] = []
        r["mapeamento"][0]["questao_id"] = "N32.a2.5.y.999"
        with self.assertRaises(Erro):
            self.base.lote(m, r)

    def test_bloqueio_e_travessia(self):
        (self.raiz / ".base.lock").touch()
        with self.assertRaises(Erro):
            self.base.registrar_metadados("N32.a2.5.y", self.mapa(2))
        for path in ("../escape", "/tmp/escape", "recursos/../../escape", "recursos\\escape"):
            with self.subTest(path=path), self.assertRaises(Erro):
                self.base.local(path)

    def test_linhas_invalidas_e_booleano(self):
        for dados in (b"\n", b'[true,"x",[]]\n', b'[0,"x",[]]', b'\xef\xbb\xbf[0,"x",[]]\n'):
            self.dados.write_bytes(dados)
            with self.subTest(dados=dados), self.assertRaises(Erro):
                self.base.validar()

    def test_chaves_duplicadas_e_nan(self):
        for valor in ('{"a":1,"a":2}', '[NaN]'):
            with self.assertRaises(Erro):
                decodificar(valor)

    def test_datas_incompletas_ou_invalidas(self):
        m = self.metadata()
        for data in ("20261114", "2026-02-30", "ontem", "2026-11-14T12:00:00"):
            m["origens"][0]["coletado_em"] = data
            with self.subTest(data=data), self.assertRaises(Erro):
                self.base.metadado("N32.a2.5.y", m)

    def test_symlink_nao_permite_sair_da_base(self):
        (self.raiz / "externo").symlink_to(Path(self.temp.name), target_is_directory=True)
        with self.assertRaises(Erro):
            self.base.local("externo/arquivo")

    def test_metadados_duplicados_e_tema_orfao(self):
        meta = self.raiz / "dados/N32/a2/5/y_md.json"
        meta.write_text('{"1":{},"1":{}}\n', encoding="utf-8")
        with self.assertRaises(Erro):
            self.base.validar()
        meta.unlink()
        meta.with_name("z_md.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(Erro):
            self.base.validar()


if __name__ == "__main__":
    unittest.main()
