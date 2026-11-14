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
from uuid import uuid4

LIMITE = 15 * 1024 * 1024
TIPOS = {"prova", "gabarito", "retificacao", "complemento"}
EXTENSOES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".json", ".jsonl", ".html", ".txt"}


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
    def __init__(self, raiz):
        self.raiz = Path(raiz).resolve()
        self.raiz.mkdir(parents=True, exist_ok=True)
        for nome in ("entrada", "recebidos"):
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
        exigir(m["id"] == lote and m["versao"] == 1, "Manifesto incompatível")
        for d in m["documentos"]:
            exigir(re.fullmatch(r"[a-f0-9]{64}", d["sha256"]) and d["arquivo"] == "originais/" + d["sha256"], "Referência inválida")
            arquivo = (p / d["arquivo"]).resolve()
            exigir(arquivo.is_relative_to(p) and arquivo.is_file(), "Original ausente")
            exigir(hashlib.sha256(arquivo.read_bytes()).hexdigest() == d["sha256"], "Original corrompido")
        provas = [d for d in m["documentos"] if d["tipo"] == "prova"]
        pendencias = [] if provas else ["Adicionar o documento de questões (prova)."]
        if not any(d["tipo"] == "gabarito" for d in m["documentos"]):
            pendencias.append("Gabarito ainda não recebido; pode ser anexado posteriormente.")
        m["pendencias"] = pendencias
        m["estado"] = "pronto_para_digitalizador" if provas else "aguardando_prova"
        m["processamento"] = "nao_iniciado"
        return m

    def criar(self, dados):
        identidade = {}
        for chave in ("prova", "edicao", "caderno"):
            exigir(isinstance(dados.get(chave), str) and 0 < len(dados[chave].strip()) <= 200, f"Informar {chave}")
            identidade[chave] = dados[chave].strip()
        for chave in ("cargo", "fonte"):
            exigir(isinstance(dados.get(chave, ""), str) and len(dados.get(chave, "")) <= 1000, f"{chave} inválido")
            identidade[chave] = dados.get(chave, "")
        lote = uuid4().hex
        with self.bloqueio():
            p = self.raiz / "recebidos" / lote
            p.mkdir()
            (p / "originais").mkdir()
            gravar(p / "lote.json", {"versao": 1, "id": lote, "criado_em": agora(), "identificacao": identidade, "documentos": []})
        return self.ler(lote)

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
        if "entrada" in dados:
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
        url = dados.get("url_origem", "")
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
                for campo in ("estado", "pendencias", "processamento"):
                    m.pop(campo, None)
                gravar(p / "lote.json", m)
            except Exception:
                destino.unlink()
                raise
        return self.ler(m["id"])

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
    parser.add_argument('comando', choices=['estado', 'criar', 'anexar'])
    args = parser.parse_args()
    try:
        c = Captador(args.raiz)
        resposta = c.estado() if args.comando == 'estado' else getattr(c, args.comando)(json.load(sys.stdin))
        print(json.dumps(resposta, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
