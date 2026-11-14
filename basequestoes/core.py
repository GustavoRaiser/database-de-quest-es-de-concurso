"""Formato v2; apenas biblioteca padrão, sem rede e sem renderizar HTML."""

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path


class Erro(ValueError):
    pass


def exigir(condicao, mensagem):
    if not condicao:
        raise Erro(mensagem)


def objeto(pares):
    resultado = {}
    for chave, valor in pares:
        exigir(chave not in resultado, f"chave JSON duplicada: {chave}")
        resultado[chave] = valor
    return resultado


def decodificar(texto):
    return json.loads(texto, object_pairs_hook=objeto,
                      parse_constant=lambda v: (_ for _ in ()).throw(Erro(f"JSON inválido: {v}")))


def ler_json(caminho):
    try:
        return decodificar(Path(caminho).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise Erro(f"{caminho}: {exc}") from exc


def linhas(caminho):
    """Não pula linhas inválidas; só LF separa registros."""
    caminho = Path(caminho)
    try:
        dados = caminho.read_bytes()
        exigir(not dados.startswith(b"\xef\xbb\xbf") and b"\r" not in dados,
               f"{caminho}: usar UTF-8 sem BOM e LF")
        exigir(not dados or dados.endswith(b"\n"), f"{caminho}: falta LF final")
        for n, texto in enumerate(dados.split(b"\n")[:-1], 1):
            try:
                exigir(bool(texto.strip()), "linha vazia")
                yield n, decodificar(texto.decode("utf-8"))
            except (ValueError, UnicodeError) as exc:
                raise Erro(f"{caminho}:{n}: {exc}") from exc
    except OSError as exc:
        raise Erro(f"{caminho}: {exc}") from exc


def serializar(valor):
    return json.dumps(valor, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n"


def atomico(caminho, conteudo):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, nome = tempfile.mkstemp(dir=caminho.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(nome, caminho)
    finally:
        if os.path.exists(nome):
            os.unlink(nome)


def texto(valor):
    return isinstance(valor, str) and bool(valor.strip())


def data_iso(valor):
    exigir(isinstance(valor, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor),
           "data inválida; usar AAAA-MM-DD")
    try:
        date.fromisoformat(valor)
    except ValueError as exc:
        raise Erro("data inválida; usar AAAA-MM-DD") from exc


def codigo(valor):
    return isinstance(valor, str) and re.fullmatch(r"(?:0|[1-9A-Za-z][0-9A-Za-z]*)", valor) is not None


def tema_valido(tema):
    exigir(isinstance(tema, str) and len(tema.split(".")) == 4
           and all(codigo(p) for p in tema.split(".")), "tema inválido")


def caminho_tema(tema, diretorio):
    tema_valido(tema)
    a, b, c, d = tema.split(".")
    return f"{diretorio}/{a}/{b}/{c}/{d}.jsonl"


def registro(valor):
    exigir(isinstance(valor, list) and len(valor) == 3, "esperado [situacao,enunciado,assertivas]")
    exigir(type(valor[0]) is int and valor[0] in (0, 1, 2), "situação inválida")
    exigir(isinstance(valor[1], str), "enunciado deve ser texto")
    exigir(isinstance(valor[2], list) and all(isinstance(x, str) for x in valor[2]),
           "assertivas devem ser lista de textos")


class Base:
    def __init__(self, raiz):
        self.raiz = Path(raiz).resolve()
        self.manifesto = ler_json(self.raiz / "manifesto.json")
        esperado = {
            "formato": "base-questoes", "versao": 2, "codificacao": "UTF-8",
            "registros": "jsonl", "campos": ["situacao", "enunciado", "assertivas"],
            "catalogos": "catalogos.json", "indice": "indice.json", "diretorio_dados": "dados",
            "diretorio_metadados": "metadados", "diretorio_recursos": "recursos",
            "diretorio_importacoes": "importacoes", "versao_metadados": 1,
        }
        exigir(isinstance(self.manifesto, dict), "manifesto deve ser objeto")
        for chave, valor in esperado.items():
            exigir(self.manifesto.get(chave) == valor, f"manifesto incompatível: {chave}")
        ids = self.manifesto.get("identificacao", {})
        exigir(isinstance(ids, dict), "identificação inválida no manifesto")
        exigir(ids.get("linha_inicial") == 1 and ids.get("linha_base") == 10
               and ids.get("alfabeto_catalogos") == "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
               "regras de identificação incompatíveis")
        self.catalogos = ler_json(self.raiz / "catalogos.json")
        self.indice = ler_json(self.raiz / "indice.json")
        exigir(isinstance(self.indice, dict) and isinstance(self.indice.get("temas"), dict), "índice inválido")

    def local(self, relativo):
        exigir(isinstance(relativo, str) and relativo and "\\" not in relativo,
               "caminho relativo inválido")
        partes = relativo.split("/")
        exigir(not Path(relativo).is_absolute() and all(p not in ("", ".", "..") for p in partes),
               "caminho fora da base")
        caminho = (self.raiz / relativo).resolve()
        exigir(caminho.is_relative_to(self.raiz), "caminho fora da base")
        return caminho

    @contextmanager
    def bloqueio(self):
        caminho = self.raiz / ".base.lock"
        try:
            fd = os.open(caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise Erro("base em gravação; se houve interrupção, verificar antes de remover .base.lock") from exc
        try:
            os.close(fd)
            yield
        finally:
            caminho.unlink()

    def questao(self, identificador):
        exigir(isinstance(identificador, str), "ID inválido")
        partes = identificador.split(".")
        exigir(len(partes) == 5 and re.fullmatch(r"[1-9][0-9]*", partes[-1]) is not None, "ID inválido")
        tema, numero = ".".join(partes[:4]), int(partes[-1])
        tema_valido(tema)
        relativo = self.indice["temas"].get(tema)
        exigir(relativo == caminho_tema(tema, "dados"), f"tema não encontrado ou caminho inválido: {tema}")
        for n, valor in linhas(self.local(relativo)):
            registro(valor)
            if n == numero:
                return valor
        raise Erro(f"questão não encontrada: {identificador}")

    def recurso(self, item):
        exigir(isinstance(item, dict), "recurso deve ser objeto")
        arquivo, digest, mime = item.get("arquivo"), item.get("sha256"), item.get("tipo_mime")
        exigir(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "SHA-256 inválido")
        exigir(arquivo == f"recursos/{digest[:2]}/{digest}", "caminho de recurso não corresponde ao hash")
        exigir(texto(mime) and re.fullmatch(r"[\w.+-]+/[\w.+-]+", mime), "tipo MIME inválido")
        conteudo = self.local(arquivo).read_bytes()
        exigir(hashlib.sha256(conteudo).hexdigest() == digest, f"recurso corrompido: {arquivo}")

    def metadado(self, tema, item):
        exigir(isinstance(item, dict) and type(item.get("questao")) is int and item["questao"] > 0,
               "metadado exige número de questão positivo")
        q = self.questao(f"{tema}.{item['questao']}")
        exigir(isinstance(item.get("textos_apoio", []), list)
               and all(isinstance(t, str) for t in item.get("textos_apoio", [])), "textos de apoio inválidos")
        origens = item.get("origens")
        exigir(isinstance(origens, list) and origens, "origens deve ser lista não vazia")
        for origem in origens:
            exigir(isinstance(origem, dict) and texto(origem.get("fonte")), "fonte obrigatória")
            exigir(texto(origem.get("coletado_em")), "data de coleta obrigatória")
            data_iso(origem["coletado_em"])
            exigir(any(texto(origem.get(k)) for k in ("id_externo", "url", "documento")),
                   "origem exige id_externo, url ou documento")
            if "documento" in origem:
                exigir(isinstance(origem["documento"], dict), "documento deve descrever recurso local")
                self.recurso(origem["documento"])
            if "pagina" in origem:
                exigir(type(origem["pagina"]) is int and origem["pagina"] > 0, "página inválida")
        if "gabarito" in item:
            g = item["gabarito"]
            exigir(isinstance(g, dict), "gabarito inválido")
            exigir(g.get("situacao") in ("ausente", "preliminar", "definitivo", "anulado"), "situação do gabarito inválida")
            respostas = g.get("alternativas_corretas")
            exigir(isinstance(respostas, list) and all(type(i) is int and 1 <= i <= len(q[2]) for i in respostas),
                   "posição de alternativa correta inválida")
            exigir(len(set(respostas)) == len(respostas), "respostas repetidas")
            exigir((bool(respostas) if g["situacao"] in ("preliminar", "definitivo") else not respostas),
                   "gabarito incompatível com sua situação")
            exigir(isinstance(g.get("rotulos_originais", []), list)
                   and all(isinstance(v, str) for v in g.get("rotulos_originais", [])), "rótulos inválidos")
            if g["situacao"] == "anulado":
                exigir(q[0] == 2, "gabarito anulado exige situação 2 na questão")
        recursos = item.get("recursos", [])
        exigir(isinstance(recursos, list), "recursos deve ser lista")
        lugares = set()
        for recurso in recursos:
            self.recurso(recurso)
            posicao = recurso.get("posicao")
            exigir(posicao in ("antes_enunciado", "apos_enunciado", "assertiva", "texto_apoio", "original"), "posição de recurso inválida")
            ordem = recurso.get("ordem")
            exigir(type(ordem) is int and ordem > 0, "ordem de recurso inválida")
            indice = recurso.get("indice")
            if posicao in ("assertiva", "texto_apoio"):
                limite = len(q[2]) if posicao == "assertiva" else len(item.get("textos_apoio", []))
                exigir(type(indice) is int and 1 <= indice <= limite, "índice de destino do recurso inválido")
            else:
                exigir(indice is None, "índice só é usado para assertiva ou texto_apoio")
            chave = (posicao, indice, ordem)
            exigir(chave not in lugares, "posição/ordem de recurso repetida")
            lugares.add(chave)
        exigir(isinstance(item.get("textos_apoio", []), list)
               and all(isinstance(t, str) for t in item.get("textos_apoio", [])), "textos de apoio inválidos")

    def metadados(self, tema):
        caminho = self.local(caminho_tema(tema, "metadados"))
        resultado = {}
        if caminho.exists():
            for n, item in linhas(caminho):
                try:
                    self.metadado(tema, item)
                    exigir(item["questao"] not in resultado, "metadado duplicado para questão")
                    resultado[item["questao"]] = item
                except (ValueError, OSError) as exc:
                    raise Erro(f"{caminho}:{n}: {exc}") from exc
        return resultado

    def consultar(self, identificador):
        q = self.questao(identificador)
        tema, numero = identificador.rsplit(".", 1)
        return {"id": identificador, "questao": q,
                "metadados": self.metadados(tema).get(int(numero))}

    def guardar_recurso(self, arquivo, mime):
        conteudo = Path(arquivo).read_bytes()
        digest = hashlib.sha256(conteudo).hexdigest()
        item = {"arquivo": f"recursos/{digest[:2]}/{digest}", "sha256": digest, "tipo_mime": mime}
        exigir(texto(mime) and re.fullmatch(r"[\w.+-]+/[\w.+-]+", mime), "tipo MIME inválido")
        with self.bloqueio():
            destino = self.local(item["arquivo"])
            if destino.exists():
                exigir(destino.read_bytes() == conteudo, "recurso existente corrompido")
            else:
                atomico(destino, conteudo)
        return item

    def registrar_metadados(self, tema, itens):
        exigir(isinstance(itens, list) and itens, "fornecer lista não vazia de metadados")
        with self.bloqueio():
            self.validar()
            existentes = self.metadados(tema)
            for item in itens:
                self.metadado(tema, item)
                exigir(item["questao"] not in existentes, "questão já possui metadados; não sobrescrever")
                existentes[item["questao"]] = item
            conteudo = "".join(serializar(v) for v in existentes.values()).encode("utf-8")
            atomico(self.local(caminho_tema(tema, "metadados")), conteudo)
        return len(itens)

    def lote(self, manifesto, relatorio):
        exigir(isinstance(manifesto, dict) and isinstance(relatorio, dict), "lote inválido")
        nome = manifesto.get("id")
        exigir(isinstance(nome, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", nome), "ID de lote inválido")
        for campo in ("fonte", "coletado_em", "versao_importador"):
            exigir(texto(manifesto.get(campo)), f"lote exige {campo}")
        data_iso(manifesto["coletado_em"])
        documentos = manifesto.get("documentos")
        exigir(isinstance(documentos, list) and documentos, "documentos do lote obrigatórios")
        for documento in documentos:
            self.recurso(documento)
            exigir(texto(documento.get("url")), "URL de origem do documento obrigatória")
        exigir(relatorio.get("pendencias") == [], "lote com pendências não pode ser registrado como concluído")
        mapa = relatorio.get("mapeamento")
        exigir(isinstance(mapa, list) and mapa, "mapeamento obrigatório")
        originais, destinos = set(), set()
        for item in mapa:
            exigir(isinstance(item, dict) and texto(item.get("numero_original")), "número original obrigatório")
            self.questao(item.get("questao_id"))
            exigir(item["numero_original"] not in originais and item["questao_id"] not in destinos, "mapeamento duplicado")
            originais.add(item["numero_original"])
            destinos.add(item["questao_id"])
        # Exclui ID local, data e nome do lote para detectar reenvio com outro nome.
        identidade = {"fonte": manifesto["fonte"],
                      "documentos": sorted(d["sha256"] for d in documentos),
                      "numeros": sorted(originais)}
        return hashlib.sha256(serializar(identidade).encode()).hexdigest()

    def registrar_lote(self, manifesto, relatorio):
        with self.bloqueio():
            self.validar()
            fingerprint = self.lote(manifesto, relatorio)
            pai = self.local("importacoes")
            for anterior in pai.glob("*/manifesto.json"):
                exigir(ler_json(anterior).get("fingerprint") != fingerprint, "lote já registrado com esse conteúdo")
            destino = self.local(f"importacoes/{manifesto['id']}")
            exigir(not destino.exists(), "ID de lote já existe")
            pai.mkdir(parents=True, exist_ok=True)
            temporario = Path(tempfile.mkdtemp(prefix=".lote-", dir=pai))
            try:
                atomico(temporario / "manifesto.json", serializar(dict(manifesto, fingerprint=fingerprint)).encode())
                atomico(temporario / "relatorio.json", serializar(relatorio).encode())
                os.rename(temporario, destino)
            finally:
                if temporario.exists():
                    for p in temporario.iterdir():
                        p.unlink()
                    temporario.rmdir()
        return manifesto["id"]

    def validar(self):
        grupos = ("orgaos", "cargos", "disciplinas", "temas")
        exigir(isinstance(self.catalogos, dict), "catálogos inválidos")
        for nivel, grupo in enumerate(grupos, 1):
            entradas = self.catalogos.get(grupo)
            exigir(isinstance(entradas, dict), f"catálogo inválido: {grupo}")
            for chave, nome in entradas.items():
                partes = chave.split(".")
                exigir(len(partes) == nivel and all(codigo(p) for p in partes) and texto(nome), f"categoria inválida: {chave}")
                if nivel > 1:
                    exigir(".".join(partes[:-1]) in self.catalogos[grupos[nivel-2]], f"categoria sem pai: {chave}")
        exigir(set(self.indice["temas"]) == set(self.catalogos["temas"]), "índice diverge dos temas cadastrados")
        quantidade, metas = 0, 0
        previstos = set()
        for tema, caminho in self.indice["temas"].items():
            exigir(caminho == caminho_tema(tema, "dados"), f"caminho inválido: {tema}")
            previstos.add(self.local(caminho))
            for n, q in linhas(self.local(caminho)):
                try:
                    registro(q)
                except Erro as exc:
                    raise Erro(f"{caminho}:{n}: {exc}") from exc
                quantidade += 1
            metas += len(self.metadados(tema))
        encontrados = {p.resolve() for p in self.local("dados").rglob("*.jsonl")}
        exigir(encontrados == previstos, "há arquivos de questões sem índice")
        for p in self.local("metadados").rglob("*.jsonl"):
            partes = p.relative_to(self.local("metadados")).with_suffix("").parts
            exigir(len(partes) == 4 and ".".join(partes) in self.indice["temas"], f"metadados de tema desconhecido: {p}")
        fingerprints = set()
        lotes = 0
        for pasta in self.local("importacoes").glob("*"):
            if not pasta.is_dir():
                continue
            m = ler_json(pasta / "manifesto.json")
            r = ler_json(pasta / "relatorio.json")
            exigir(m.get("id") == pasta.name, "ID de lote diverge da pasta")
            fingerprint = self.lote(m, r)
            exigir(m.get("fingerprint") == fingerprint, "fingerprint de lote inválido")
            exigir(fingerprint not in fingerprints, "lote duplicado")
            fingerprints.add(fingerprint)
            lotes += 1
        return {"temas": len(previstos), "questoes": quantidade, "metadados": metas, "lotes": lotes}
