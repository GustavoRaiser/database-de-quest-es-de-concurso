"""API pública por CLI JSON: recebe materiais, sem extrair questões."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
import unicodedata
from uuid import uuid4

LIMITE = 15 * 1024 * 1024
TIPOS = {"prova", "gabarito", "retificacao", "complemento"}
EXTENSOES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".json", ".jsonl", ".html", ".txt"}
ALFABETO = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CAMPOS = ('prova', 'edicao', 'caderno', 'orgao_id', 'cargo_id', 'orgao', 'cargo', 'banca', 'ano',
          'escolaridade', 'area_atuacao', 'area_formacao', 'uf', 'esfera', 'etapa', 'data_aplicacao', 'edital', 'fonte')


def normalizar(valor):
    return ' '.join(unicodedata.normalize('NFC', valor).casefold().split())


def base62(n):
    if n == 0:
        return '0'
    resultado = ''
    while n:
        n, resto = divmod(n, 62)
        resultado = ALFABETO[resto] + resultado
    return resultado


def validar_identidade(dados):
    identidade = {}
    for chave in CAMPOS:
        valor = dados.get(chave, '')
        exigir(isinstance(valor, str) and len(valor) <= 1000, f'{chave} inválido')
        identidade[chave] = valor.strip()
    for chave in ('prova', 'edicao', 'caderno', 'orgao_id', 'cargo_id', 'orgao', 'cargo', 'banca', 'ano'):
        exigir(bool(identidade[chave]), f'Informar {chave}')
    for chave in ('orgao_id', 'cargo_id'):
        exigir(re.fullmatch(r'(?:0|[1-9A-Za-z][0-9A-Za-z]*)', identidade[chave]), f'{chave}: usar código base 62 sem zeros à esquerda')
    exigir(re.fullmatch(r'[0-9]{4}', identidade['ano']), 'Ano deve conter quatro dígitos')
    exigir(not identidade['uf'] or identidade['uf'] in 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(), 'UF inválida')
    if identidade['data_aplicacao']:
        from datetime import date
        exigir(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', identidade['data_aplicacao']), 'Data: usar AAAA-MM-DD')
        date.fromisoformat(identidade['data_aplicacao'])
    return identidade


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def agora():
    return datetime.now(timezone.utc).isoformat()


def gravar(path, objeto):
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(objeto, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Captador:
    def __init__(self, raiz, catalogos=None):
        self.raiz = Path(raiz).resolve()
        self.raiz.mkdir(parents=True, exist_ok=True)
        self.catalogos = json.loads(Path(catalogos).read_text(encoding='utf-8')) if catalogos else {'orgaos': {}, 'cargos': {}}
        for nome in ("entrada", "recebidos", "encaminhamentos"):
            p = self.raiz / nome
            exigir(not p.is_symlink(), "Diretório não pode ser link simbólico")
            p.mkdir(exist_ok=True)

    @contextmanager
    def bloqueio(self):
        lock = self.raiz / ".captador.lock"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        try:
            yield
        finally:
            lock.unlink()

    def pasta(self, lote):
        exigir(isinstance(lote, str) and re.fullmatch(r"[a-f0-9]{32}", lote), "ID de lote inválido")
        p = self.raiz / "recebidos" / lote
        exigir(not p.is_symlink() and p.is_dir(), "Lote não encontrado")
        return p

    def ler(self, lote):
        p = self.pasta(lote)
        exigir(not (p / "lote.json").is_symlink(), "Manifesto inválido")
        m = json.loads((p / "lote.json").read_text(encoding="utf-8"))
        exigir(m["id"] == lote and m["versao"] in (1, 2), "Manifesto incompatível")
        for d in m["documentos"]:
            exigir(re.fullmatch(r"[a-f0-9]{64}", d["sha256"]) and d["arquivo"] == "originais/" + d["sha256"], "Referência inválida")
            arquivo = (p / d["arquivo"]).resolve()
            exigir(arquivo.is_relative_to(p) and arquivo.is_file(), "Original ausente")
            exigir(hashlib.sha256(arquivo.read_bytes()).hexdigest() == d["sha256"], "Original corrompido")
        provas = [d for d in m["documentos"] if d["tipo"] == "prova"]
        exigir(len(provas) <= 1, 'Lote possui mais de uma prova')
        gabaritos = [d for d in m['documentos'] if d['tipo'] == 'gabarito']
        for d in gabaritos:
            exigir(provas and d.get('referente_a') == provas[0]['sha256'], 'Gabarito não corresponde à prova do lote')
            exigir(d.get('situacao_gabarito') in ('preliminar', 'definitivo'), 'Situação do gabarito inválida')
        pendencias = [] if provas else ["Adicionar o documento de questões (prova)."]
        if not gabaritos:
            pendencias.append("Adicionar gabarito vinculado: encaminhamento bloqueado.")
        if m['versao'] == 2:
            i = validar_identidade(m['identificacao'])
            prefixo = i['orgao_id'] + '.' + i['cargo_id']
            exigir(m.get('grupo') == prefixo and isinstance(m.get('protocolo'), str)
                   and re.fullmatch(re.escape(prefixo) + r'\.(?:0|[1-9A-Za-z][0-9A-Za-z]*)', m['protocolo']), 'Protocolo inválido')
        else:
            pendencias.append('Identificar órgão, cargo, banca e ano para obter protocolo.')
        m["pendencias"] = pendencias
        m['liberado'] = bool(provas and gabaritos and m['versao'] == 2)
        m["estado"] = ('pronto_para_digitalizador' if m['liberado'] else
                       'aguardando_prova' if not provas else 'aguardando_gabarito' if not gabaritos else 'aguardando_identificacao')
        m['processamento'] = ('analise_registrada' if m.get('analise') else
                              'aguardando_digitalizador' if m.get('encaminhamento') else 'nao_iniciado')
        if m.get('extracao', {}).get('encaminhamento') == m.get('encaminhamento') and m.get('extracao'):
            m['processamento'] = m['extracao']['estado']
        return m

    def registrar_identidade(self, identidade, ignorar=None):
        grupo = identidade['orgao_id'] + '.' + identidade['cargo_id']
        for campo, nome, mapa in [('orgao_id', 'orgao', 'orgaos'), ('cargo_id', 'cargo', 'cargos')]:
            codigo = identidade[campo] if mapa == 'orgaos' else grupo
            existente = self.catalogos[mapa].get(codigo)
            exigir(not existente or normalizar(existente) == normalizar(identidade[nome]), f'{nome}: código conflita com catálogo do Organizador')
        usados = set()
        chave = ('orgao_id', 'cargo_id', 'prova', 'banca', 'ano', 'edicao', 'caderno', 'etapa')
        for p in (self.raiz / 'recebidos').iterdir():
            if not p.is_dir() or p.name == ignorar:
                continue
            anterior = self.ler(p.name)  # Falha fechada se outro protocolo estiver corrompido.
            i = anterior['identificacao']
            if anterior['versao'] != 2:
                continue
            for codigo, nome in [('orgao_id', 'orgao'), ('cargo_id', 'cargo')]:
                mesmo = i.get(codigo) == identidade[codigo]
                if codigo == 'cargo_id':
                    mesmo = mesmo and i.get('orgao_id') == identidade['orgao_id']
                exigir(not mesmo or normalizar(i[nome]) == normalizar(identidade[nome]), f'{nome}: código já registrado com outro nome')
            exigir(any(normalizar(i[k]) != normalizar(identidade[k]) for k in chave),
                   f"Prova já registrada: {anterior.get('protocolo')}; retome o lote {anterior['id']}")
            if anterior['grupo'] == grupo:
                usados.add(anterior['protocolo'].rsplit('.', 1)[1])
        numero = 0
        while base62(numero) in usados:
            numero += 1
        return grupo, grupo + '.' + base62(numero)

    def criar(self, dados):
        identidade = validar_identidade(dados)
        lote = uuid4().hex
        with self.bloqueio():
            grupo, protocolo = self.registrar_identidade(identidade)
            p = self.raiz / "recebidos" / lote
            p.mkdir()
            (p / "originais").mkdir()
            gravar(p / "lote.json", {"versao": 2, "id": lote, "grupo": grupo, "protocolo": protocolo,
                                      "criado_em": agora(), "identificacao": identidade, "documentos": [],
                                      "historico": [{'evento': 'registrado', 'em': agora()}]})
        return self.ler(lote)

    def identificar(self, dados):
        identidade = validar_identidade(dados)
        with self.bloqueio():
            m = self.ler(dados.get('lote'))
            exigir(m['versao'] == 1, 'Identificação é apenas para lotes antigos sem protocolo')
            grupo, protocolo = self.registrar_identidade(identidade, m['id'])
            m.update(versao=2, grupo=grupo, protocolo=protocolo, identificacao=identidade,
                     historico=[{'evento': 'identificado_lote_legado', 'em': agora()}])
            gravar(self.pasta(m['id']) / 'lote.json', m)
        return self.ler(m['id'])

    def anexar(self, dados):
        nome = dados.get("nome")
        exigir(isinstance(nome, str) and nome and len(nome) <= 240 and '/' not in nome and '\\' not in nome,
               "Nome de arquivo inválido")
        exigir(Path(nome).suffix.lower() in EXTENSOES, "Formato de arquivo não suportado")
        tipo = dados.get("tipo")
        exigir(tipo in TIPOS, "Tipo de documento inválido")
        situacao = dados.get("situacao_gabarito", "")
        exigir(situacao in ("preliminar", "definitivo") if tipo == "gabarito" else situacao == "",
               "Informar preliminar/definitivo apenas para gabaritos")
        rede = None
        if 'url' in dados:
            from rede import obter
            conteudo, rede = obter(dados['url'])
            exigir(conteudo.startswith(b'%PDF-'), 'O endereço deve apontar diretamente para um PDF')
            canal = 'url'
        elif "entrada" in dados:
            exigir(dados["entrada"] == nome, "Selecionar nome da pasta de entrada")
            p = self.raiz / "entrada" / nome
            exigir(not p.is_symlink() and p.is_file(), "Arquivo de entrada não encontrado")
            exigir(p.stat().st_size <= LIMITE, "Arquivo excede 15 MiB")
            conteudo = p.read_bytes()
            canal = "pasta"
        else:
            valor = dados.get("conteudo_base64", "")
            exigir(isinstance(valor, str) and len(valor) <= LIMITE * 4 // 3 + 4, "Arquivo excede 15 MiB")
            conteudo = base64.b64decode(valor, validate=True)
            canal = "upload"
        exigir(0 < len(conteudo) <= LIMITE, "Arquivo vazio ou acima de 15 MiB")
        sha = hashlib.sha256(conteudo).hexdigest()
        url = dados.get('url', dados.get("url_origem", ""))
        exigir(isinstance(url, str) and len(url) <= 2000, "URL de origem inválida")
        with self.bloqueio():
            m = self.ler(dados.get("lote"))
            exigir(not any(d["sha256"] == sha for d in m["documentos"]), "Arquivo já recebido neste lote")
            provas = [d for d in m["documentos"] if d["tipo"] == "prova"]
            exigir(tipo != "prova" or not provas, "Um lote corresponde a uma prova/caderno; crie outro lote")
            exigir(tipo not in ("gabarito", "retificacao") or provas, "Anexar a prova antes do gabarito/retificação")
            d = {"nome_original": nome, "arquivo": "originais/" + sha, "sha256": sha,
                 "tamanho": len(conteudo), "tipo": tipo, "situacao_gabarito": situacao,
                 "referente_a": provas[0]["sha256"] if provas and tipo in ("gabarito", "retificacao") else None,
                 "recebido_em": agora(), "canal": canal, "url_origem": url}
            if rede:
                d['download'] = rede
            p = self.pasta(m["id"])
            exigir(not (p / "originais").is_symlink(), "Pasta de originais inválida")
            destino = p / d["arquivo"]
            exigir(not destino.exists(), "Original já existe; conferir lote antes de repetir")
            with destino.open("xb") as f:
                f.write(conteudo)
                f.flush()
                os.fsync(f.fileno())
            try:
                m["documentos"].append(d)
                m.pop('encaminhamento', None)
                m.pop('analise', None)
                m.pop('extracao', None)
                m.setdefault('historico', []).append({'evento':'documento_recebido','em':agora(),'sha256':sha,'tipo':tipo})
                for campo in ("estado", "pendencias", "processamento"):
                    m.pop(campo, None)
                gravar(p / "lote.json", m)
            except Exception:
                destino.unlink()
                raise
        return self.ler(m["id"])

    def encaminhar(self, dados):
        with self.bloqueio():
            m = self.ler(dados.get('lote'))
            exigir(m['liberado'], 'Encaminhamento bloqueado: exige identificação, prova e gabarito íntegros e vinculados')
            gabaritos = [d for d in m['documentos'] if d['tipo'] == 'gabarito']
            escolhido = dados.get('gabarito_sha256')
            exigir(isinstance(escolhido, str), 'Selecionar explicitamente o gabarito para encaminhar')
            g = next((d for d in gabaritos if d['sha256'] == escolhido), None)
            exigir(g is not None, 'Gabarito não pertence a este lote')
            prova = next(d for d in m['documentos'] if d['tipo'] == 'prova')
            pacote = {'versao':1, 'lote':m['id'], 'protocolo':m['protocolo'], 'identificacao':m['identificacao'],
                      'prova':prova, 'gabarito':g, 'complementos':[d for d in m['documentos'] if d['tipo'] in ('retificacao','complemento')],
                      'raiz_originais':'recebidos/' + m['id']}
            digest = hashlib.sha256(json.dumps(pacote,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            path = self.raiz / 'encaminhamentos' / (digest + '.json')
            exigir(not path.is_symlink(), 'Encaminhamento inválido')
            if path.exists():
                exigir(json.loads(path.read_text(encoding='utf-8'))['pacote'] == pacote, 'Encaminhamento corrompido')
            else:
                gravar(path, {'criado_em':agora(), 'id':digest, 'pacote':pacote})
            if m.get('encaminhamento') != digest:
                m['encaminhamento'] = digest
                m.pop('analise', None)
                m.pop('extracao', None)
                m.setdefault('historico',[]).append({'evento':'encaminhado','em':agora(),'id':digest})
                gravar(self.pasta(m['id']) / 'lote.json', m)
        return {'id':digest, 'arquivo':'encaminhamentos/'+digest+'.json', 'protocolo':m['protocolo'], 'estado':'aguardando_digitalizador'}

    def registrar_analise(self, dados):
        with self.bloqueio():
            m = self.ler(dados.get('lote'))
            exigir(m['liberado'] and m.get('encaminhamento') and dados.get('encaminhamento') == m['encaminhamento'], 'Informar encaminhamento válido do lote completo')
            exigir(dados.get('resultado') in ('concluida','falha') and isinstance(dados.get('relatorio'),str) and dados['relatorio'].strip(), 'Informar resultado e relatório da análise')
            m['analise'] = {'resultado':dados['resultado'], 'relatorio':dados['relatorio'], 'em':agora(),
                            'encaminhamento':m['encaminhamento'], 'declarada_por':'usuario'}
            m.setdefault('historico',[]).append(dict(m['analise'], evento='analise_registrada'))
            gravar(self.pasta(m['id']) / 'lote.json', m)
        return self.ler(m['id'])

    def entrega(self, dados):
        with self.bloqueio():
            m = self.ler(dados.get('lote'))
            exigir(m['liberado'] and m.get('encaminhamento'), 'Lote incompleto ou não encaminhado')
            id_ = m['encaminhamento']
            exigir(re.fullmatch('[a-f0-9]{64}', id_) and dados.get('encaminhamento', id_) == id_, 'Encaminhamento inválido ou obsoleto')
            path = self.raiz / 'encaminhamentos' / (id_ + '.json')
            exigir(not path.is_symlink(), 'Pacote inválido')
            envelope = json.loads(path.read_text(encoding='utf-8'))
            pacote = envelope['pacote']
            digest = hashlib.sha256(json.dumps(pacote, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            exigir(digest == id_ and envelope['id'] == id_, 'Pacote corrompido')
            exigir(pacote['lote'] == m['id'] and pacote['identificacao'] == m['identificacao'], 'Identificação divergente')
            exigir(pacote['prova'] in m['documentos'] and pacote['gabarito'] in m['documentos'], 'Documentos divergentes')
            return envelope

    def registrar_extracao(self, dados):
        with self.bloqueio():
            m = self.ler(dados.get('lote'))
            exigir(m['liberado'] and m.get('encaminhamento') == dados.get('encaminhamento') and m.get('encaminhamento'), 'Lote incompleto ou encaminhamento obsoleto')
            exigir(isinstance(dados.get('resultado_id'), str) and re.fullmatch('[a-f0-9]{64}', dados['resultado_id']), 'Resultado inválido')
            exigir(dados.get('estado') in ('extraido', 'extraido_com_pendencias') and isinstance(dados.get('contagens'), dict), 'Estado de extração inválido')
            if m.get('extracao', {}).get('resultado_id') != dados['resultado_id']:
                m['extracao'] = {k:dados[k] for k in ('resultado_id','encaminhamento','estado','contagens')}
                m['extracao']['em'] = agora()
                m.setdefault('historico', []).append(dict(m['extracao'], evento='extracao_programatica'))
                gravar(self.pasta(m['id'])/'lote.json', m)
        return self.ler(m['id'])

    def estado(self):
        lotes, erros = [], []
        for p in sorted((self.raiz / "recebidos").iterdir()):
            if p.is_dir():
                try:
                    lotes.append(self.ler(p.name))
                except (OSError, ValueError, KeyError) as e:
                    erros.append({"lote": p.name, "erro": str(e)})
        entrada = [{"nome": p.name, "tamanho": p.stat().st_size} for p in sorted((self.raiz / "entrada").iterdir())
                   if p.is_file() and not p.is_symlink() and p.suffix.lower() in EXTENSOES]
        return {"lotes": lotes, "entrada": entrada, "erros": erros}


def main():
    parser = argparse.ArgumentParser(description="Captador de materiais originais")
    parser.add_argument('--raiz', type=Path, default=Path(__file__).parent / 'trabalho')
    parser.add_argument('--catalogos', type=Path, help='catálogos do Organizador para conferir códigos existentes')
    parser.add_argument('comando', choices=['estado', 'criar', 'anexar', 'identificar', 'encaminhar', 'registrar_analise', 'descobrir', 'entrega', 'registrar_extracao'])
    args = parser.parse_args()
    try:
        c = Captador(args.raiz, args.catalogos)
        if args.comando == 'descobrir':
            from rede import descobrir
            resposta = descobrir(json.load(sys.stdin)['url'])
        else:
            resposta = c.estado() if args.comando == 'estado' else getattr(c, args.comando)(json.load(sys.stdin))
        print(json.dumps(resposta, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
