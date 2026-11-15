"""Visualização local e API de leitura. Python 3.10+, biblioteca padrão."""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlsplit

MODULO = Path(__file__).resolve().parent
ORGANIZADOR = MODULO.parent / "organizador"


def consultar(base, comando, argumentos=()):
    processo = subprocess.run([sys.executable, "-m", "basequestoes", "--base", str(base), comando, *argumentos],
                              cwd=ORGANIZADOR, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if processo.returncode:
        raise ValueError(processo.stderr.strip())
    return json.loads(processo.stdout)


def criar_servidor(base, porta=8000, captacoes=None, digitalizacoes=None):
    base = Path(base).resolve()
    consultar(base, "validar")
    captacoes = Path(captacoes or MODULO.parent / "captador/trabalho").resolve()
    token = secrets.token_urlsafe(32)
    digitalizacoes = Path(digitalizacoes or MODULO.parent/'digitalizador/trabalho').resolve()
    processamento = threading.BoundedSemaphore(1)

    def captar(comando, dados=None):
        p = subprocess.run([sys.executable, str(MODULO.parent / "captador/app.py"),
                            "--raiz", str(captacoes), "--catalogos", str(base / 'catalogos.json'), comando],
                           input=json.dumps(dados), capture_output=True, text=True, encoding="utf-8", timeout=120)
        if p.returncode:
            raise ValueError(p.stderr.strip())
        return json.loads(p.stdout)

    class Handler(BaseHTTPRequestHandler):
        def responder(self, status, dados, mime="application/json; charset=utf-8", download=False):
            corpo = json.dumps(dados, ensure_ascii=False).encode() if isinstance(dados, dict) else dados
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            if download:
                self.send_header("Content-Disposition", "attachment")
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            if urlsplit('//' + self.headers.get('Host', '')).hostname not in ('127.0.0.1', 'localhost'):
                self.responder(403, {"erro": "Host inválido"})
                return
            url = urlsplit(self.path)
            try:
                if url.path in ("/", "/app.js", "/captacao.js", "/style.css"):
                    arquivo, mime = {"/": ("index.html", "text/html; charset=utf-8"),
                                     "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                                     "/captacao.js": ("captacao.js", "text/javascript; charset=utf-8"),
                                     "/style.css": ("style.css", "text/css; charset=utf-8")}[url.path]
                    self.responder(200, (MODULO / "web" / arquivo).read_bytes(), mime)
                elif url.path == "/api/captacao":
                    self.responder(200, dict(captar("estado"), token_captacao=token))
                elif url.path == "/api/catalogos":
                    self.responder(200, consultar(base, "catalogos"))
                elif url.path == "/api/questoes":
                    params = parse_qs(url.query, keep_blank_values=True)
                    permitidos = {"orgao", "cargo", "disciplina", "tema", "pagina", "por_pagina"}
                    if set(params) - permitidos or any(len(v) != 1 for v in params.values()):
                        raise ValueError("Parâmetros desconhecidos ou repetidos")
                    args = []
                    for chave, valores in params.items():
                        if valores[0]:
                            args.append("--" + chave.replace("_", "-") + "=" + valores[0])
                    self.responder(200, consultar(base, "emitir", args))
                elif url.path.startswith("/recursos/"):
                    relativo = url.path.lstrip("/")
                    if not re.fullmatch(r"recursos/[a-f0-9]{2}/[a-f0-9]{64}", relativo):
                        raise ValueError("Caminho de recurso inválido")
                    destino = (base / relativo).resolve()
                    if not destino.is_relative_to(base) or not destino.is_file():
                        self.responder(404, {"erro": "Recurso não encontrado"})
                        return
                    corpo = destino.read_bytes()
                    if hashlib.sha256(corpo).hexdigest() != destino.name or destino.parent.name != destino.name[:2]:
                        raise ValueError("Recurso corrompido")
                    # Só formatos raster conhecidos são exibidos; HTML/SVG/PDF ficam para download.
                    mime = ("image/png" if corpo.startswith(b"\x89PNG\r\n\x1a\n") else
                            "image/jpeg" if corpo.startswith(b"\xff\xd8\xff") else
                            "image/gif" if corpo.startswith((b"GIF87a", b"GIF89a")) else
                            "application/octet-stream")
                    self.responder(200, corpo, mime, mime == "application/octet-stream")
                else:
                    self.responder(404, {"erro": "Não encontrado"})
            except (ValueError, subprocess.TimeoutExpired) as exc:
                self.responder(400, {"erro": str(exc)})
            except OSError:
                self.responder(500, {"erro": "Falha na leitura da base"})

        def do_POST(self):
            host = self.headers.get('Host', '')
            if (urlsplit('//' + host).hostname not in ('127.0.0.1', 'localhost')
                    or self.headers.get('Origin') != 'http://' + host
                    or self.headers.get('X-Captacao-Token') != token):
                self.responder(403, {"erro": "Origem ou sessão inválida; recarregue a página"})
                return
            comandos = {'/api/captacao/' + c: c for c in ('criar','anexar','identificar','encaminhar','registrar_analise','descobrir')}
            processar = self.path == '/api/digitalizacao/processar'
            if self.path not in comandos and not processar:
                self.responder(404, {"erro": "Não encontrado"})
                return
            try:
                tamanho = int(self.headers.get('Content-Length', '0'))
                if not 0 < tamanho <= 22 * 1024 * 1024:
                    raise ValueError("Envio vazio ou acima do limite de 22 MiB")
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ValueError("Enviar application/json")
                self.connection.settimeout(30)
                corpo = self.rfile.read(tamanho)
                if len(corpo) != tamanho:
                    raise ValueError("Envio incompleto")
                dados = json.loads(corpo)
                if not isinstance(dados, dict):
                    raise ValueError("Enviar um objeto JSON")
                if processar:
                    lote = dados.get('lote')
                    if not isinstance(lote, str) or not re.fullmatch('[a-f0-9]{32}', lote):
                        raise ValueError('Lote inválido')
                    if not processamento.acquire(blocking=False):
                        raise ValueError('Já existe um processamento em andamento; aguarde')
                    try:
                        p = subprocess.run([sys.executable,str(MODULO.parent/'digitalizador/app.py'),
                                            '--captacoes',str(captacoes),'--saida',str(digitalizacoes),
                                            '--base',str(base),lote],capture_output=True,text=True,encoding='utf-8',timeout=300)
                        if p.returncode:
                            raise ValueError(p.stderr.strip())
                        self.responder(200,json.loads(p.stdout))
                    finally:
                        processamento.release()
                else:
                    self.responder(200, captar(comandos[self.path], dados))
            except (ValueError, subprocess.TimeoutExpired) as exc:
                self.responder(400, {"erro": str(exc)})
            except OSError:
                self.responder(500, {"erro": "Falha ao receber material"})

    return ThreadingHTTPServer(("127.0.0.1", porta), Handler)


def main():
    parser = argparse.ArgumentParser(description="Emissor: visualizar e consultar questões")
    parser.add_argument("--base", type=Path, default=ORGANIZADOR)
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--captacoes", type=Path, help="pasta de trabalho do Captador")
    parser.add_argument('--digitalizacoes', type=Path, help='pasta de resultados do Digitalizador')
    args = parser.parse_args()
    try:
        server = criar_servidor(args.base, args.porta, args.captacoes, args.digitalizacoes)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Erro: {exc}\n")
    print(f"Emissor: http://127.0.0.1:{server.server_port} — base: {args.base.resolve()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
