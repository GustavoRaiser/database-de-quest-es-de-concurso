"""Publicação recuperável de conjuntos de arquivos. Leitores recusam estado parcial."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
from uuid import uuid4

from .core import Base, Erro, atomico, exigir, ler_json, serializar

PARTES = ('manifesto.json', 'catalogos.json', 'indice.json', 'dados', 'recursos', 'importacoes', 'provas')


def copiar_sem_alterar(origem, destino):
    try:
        os.link(origem, destino)
    except OSError:
        shutil.copy2(origem, destino)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


@contextmanager
def lock(raiz):
    path = raiz / '.base.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise Erro('base bloqueada; conferir processo antes de remover .base.lock') from exc
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def aplicar(raiz, plano):
    destino = Base.__new__(Base)
    destino.raiz = raiz
    for item in plano['arquivos']:
        alvo = destino.local(item['caminho'])
        atual = sha(alvo)
        if atual == item['novo']:
            continue
        exigir(atual == item['anterior'], 'conflito na recuperação: '+item['caminho'])
        novo = destino.local('.transacoes/'+plano['id']+'/novos/'+item['caminho'])
        exigir(sha(novo) == item['novo'], 'arquivo de recuperação ausente/corrompido')
        atomico(alvo, novo.read_bytes())
    atomico(raiz/'.revisao.json', serializar({'transacao':plano['id']}).encode())
    atomico(raiz/'.transacoes'/plano['id']/'concluida.json', serializar({'concluida':True}).encode())
    (raiz/'.transacao-pendente.json').unlink()
    shutil.rmtree(raiz/'.transacoes'/plano['id']/'novos', ignore_errors=True)


def recuperar(raiz):
    raiz = Path(raiz).resolve()
    with lock(raiz):
        pendente = raiz/'.transacao-pendente.json'
        if not pendente.exists():
            return {'recuperada':False}
        plano = ler_json(pendente)
        exigir(isinstance(plano.get('id'),str) and len(plano['id']) == 32 and all(c in '0123456789abcdef' for c in plano['id']), 'transação inválida')
        aplicar(raiz, plano)
        Base(raiz).validar()
        return {'recuperada':True, 'transacao':plano['id']}


def executar(raiz, preparar):
    raiz = Path(raiz).resolve()
    with lock(raiz):
        base = Base(raiz)
        base.validar()
        transacao = uuid4().hex
        pai = raiz/'.transacoes'/transacao
        exigir(pai.resolve().is_relative_to(raiz), 'Diretório de transações fora da base')
        novos = pai/'novos'
        novos.mkdir(parents=True)
        publicado = False
        try:
            for nome in PARTES:
                fonte = raiz/nome
                exigir(not fonte.is_symlink(), 'Não copiar links na base: '+nome)
                if fonte.is_dir():
                    exigir(not any(p.is_symlink() for p in fonte.rglob('*')), 'Não copiar links dentro de '+nome)
                    shutil.copytree(fonte, novos/nome, copy_function=copiar_sem_alterar)
                elif fonte.is_file():
                    copiar_sem_alterar(fonte, novos/nome)
            resultado = preparar(Base(novos))
            Base(novos).validar()
            arquivos = []
            for path in sorted(novos.rglob('*')):
                if path.is_file():
                    relativo = path.relative_to(novos).as_posix()
                    antes, depois = sha(raiz/relativo), sha(path)
                    if antes != depois:
                        arquivos.append({'caminho':relativo,'anterior':antes,'novo':depois})
            if not arquivos:
                return resultado
            plano = {'id':transacao,'arquivos':arquivos}
            atomico(pai/'plano.json', serializar(plano).encode())
            atomico(raiz/'.transacao-pendente.json', serializar(plano).encode())
            publicado = True
            aplicar(raiz, plano)
            return resultado
        finally:
            if not publicado:
                shutil.rmtree(pai, ignore_errors=True)
