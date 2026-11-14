"""Visualização local e API de leitura. Python 3.10+, biblioteca padrão."""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

MODULO = Path(__file__).resolve().parent
ORGANIZADOR = MODULO.parent / "organizador"


def consultar(base, comando, argumentos=()):
    processo = subprocess.run([sys.executable, "-m", "basequestoes", "--base", str(base), comando, *argumentos],
                              cwd=ORGANIZADOR, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if processo.returncode:
        raise ValueError(processo.stderr.strip())
    return json.loads(processo.stdout)


def criar_servidor(base, porta=8000):
    base = Path(base).resolve()
    consultar(base, "validar")

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
            url = urlsplit(self.path)
            try:
                if url.path in ("/", "/app.js", "/style.css"):
                    arquivo, mime = {"/": ("index.html", "text/html; charset=utf-8"),
                                     "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                                     "/style.css": ("style.css", "text/css; charset=utf-8")}[url.path]
                    self.responder(200, (MODULO / "web" / arquivo).read_bytes(), mime)
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

    return ThreadingHTTPServer(("127.0.0.1", porta), Handler)


def main():
    parser = argparse.ArgumentParser(description="Emissor: visualizar e consultar questões")
    parser.add_argument("--base", type=Path, default=ORGANIZADOR)
    parser.add_argument("--porta", type=int, default=8000)
    args = parser.parse_args()
    try:
        server = criar_servidor(args.base, args.porta)
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
