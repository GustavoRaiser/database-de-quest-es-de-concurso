"""Extrator local e determinístico de um formato ENAM/FGV explicitamente suportado."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DISCIPLINAS = {'DIREITO CONSTITUCIONAL', 'DIREITO ADMINISTRATIVO', 'DIREITO CIVIL',
               'DIREITO EMPRESARIAL', 'DIREITO PENAL', 'DIREITO PROCESSUAL CIVIL', 'DIREITOS HUMANOS'}


def exigir(ok, mensagem):
    if not ok:
        raise ValueError(mensagem)


def cli(cmd, dados, cwd=None):
    p = subprocess.run(cmd, input=json.dumps(dados, ensure_ascii=False), capture_output=True,
                       text=True, encoding='utf-8', cwd=cwd, timeout=180)
    exigir(p.returncode == 0, p.stderr.strip() or 'Ferramenta retornou erro')
    return json.loads(p.stdout)


def separar(blocos, esperado=80):
    qs, q, disciplina = [], None, None
    for b in blocos:
        for linha in b['texto'].splitlines():
            linha = linha.strip()
            if re.fullmatch(r'TIPO 1 [–-] PÁGINA \d+', linha):
                continue
            if linha in DISCIPLINAS:
                disciplina = linha
                continue
            if linha == 'NOÇÕES GERAIS DE DIREITO E FORMAÇÃO':
                disciplina = 'NOÇÕES GERAIS DE DIREITO E FORMAÇÃO HUMANÍSTICA'
                continue
            if linha == 'HUMANÍSTICA':
                continue
            if re.fullmatch(r'[1-9][0-9]?', linha):
                if q:
                    qs.append(q)
                q = {'numero_original': linha, 'disciplina': disciplina, 'paginas': [b['pagina']], 'linhas': []}
            elif q:
                q['linhas'].append(linha)
                if linha and b['pagina'] not in q['paginas']:
                    q['paginas'].append(b['pagina'])
            elif linha:
                raise ValueError('Conteúdo antes da primeira questão não reconhecido: layout não suportado')
    if q:
        qs.append(q)
    exigir([int(q['numero_original']) for q in qs] == list(range(1, esperado+1)), 'Numeração incompleta ou fora de ordem; extração recusada')
    for q in qs:
        partes = re.split(r'^\(([A-E])\)\s*', '\n'.join(q.pop('linhas')), flags=re.M)
        q['enunciado'] = partes[0].strip()
        q['rotulos_originais'] = partes[1::2]
        q['assertivas'] = [s.strip() for s in partes[2::2]]
        exigir(q['rotulos_originais'] == list('ABCDE') and q['enunciado'] and all(q['assertivas']),
               f"Questão {q['numero_original']}: enunciado/alternativas incompletos")
        q['pendencias'] = [] if q['disciplina'] else ['Disciplina não identificada no cabeçalho']
    return qs


def respostas_tipo1(texto, esperado=80):
    blocos = re.split(r'ENAM\s*[–-]\s*Exame Nacional da Magistratura\s*-\s*Prova Tipo\s*', texto)
    tipo1 = [b for b in blocos[1:] if re.match(r'1\b', b)]
    exigir(len(tipo1) == 1, 'Bloco do gabarito Tipo 1 não identificado inequivocamente')
    pares = re.findall(r'^\s*([1-9][0-9]?)\s*\n\s*([A-E*])\s*$', tipo1[0], flags=re.M)
    exigir(len(pares) == esperado and [int(n) for n, _ in pares] == list(range(1, esperado+1)),
           'Gabarito incompleto ou com numeração duplicada')
    if any(letra == '*' for _, letra in pares):
        exigir('Questão Anulada' in tipo1[0], 'Marcador de anulação sem legenda conhecida')
    return dict(pares)


def extrair(prova, gabarito, edicao=None):
    try:
        import pdfplumber
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError('Instale: python -m pip install -r digitalizador/requirements.txt') from exc
    blocos, visuais = [], []
    with pdfplumber.open(prova) as pdf:
        exigir(len(pdf.pages) >= 3, 'Prova curta demais para o perfil ENAM')
        # A tipografia da capa pode fragmentar TIPO entre fontes no pdfplumber.
        capa = PdfReader(prova).pages[0].extract_text() or ''
        exigir(re.search(r'ENAM\s*[–-]\s*202\d', capa) and re.search(r'TIPO\s*1\b', capa),
               'Capa não corresponde ao perfil ENAM Tipo 1')
        if edicao:
            m = re.search(r'ENAM\s*[–-]\s*(202\d\.\d+)', capa)
            exigir(m and m.group(1) == edicao, 'Edição da capa diverge da identificação do lote')
        for numero, p in enumerate(pdf.pages[2:], 3):
            exigir(p.width > 400 and p.height > 600, 'Dimensões de página não suportadas')
            if not (p.extract_text() or '').strip():
                raise ValueError(f'Página {numero} sem texto; OCR não implementado')
            corpo = p.crop((0, 60, p.width, p.height-65))
            # Imagens e vetores no corpo devem ser conferidos no original.
            if corpo.images or corpo.curves or corpo.rects:
                visuais.append(numero)
            for x0, x1 in ((0, p.width/2), (p.width/2, p.width)):
                blocos.append({'pagina': numero, 'texto': p.crop((x0,60,x1,p.height-40)).extract_text() or ''})
    qs = separar(blocos)
    texto = '\n'.join(p.extract_text() or '' for p in PdfReader(gabarito).pages)
    respostas = respostas_tipo1(texto)
    for q in qs:
        letra = respostas[q['numero_original']]
        q['gabarito'] = {'situacao': 'anulado' if letra == '*' else 'informado_na_fonte',
                         'alternativas_corretas': [] if letra == '*' else [list('ABCDE').index(letra)+1],
                         'rotulos_originais': [] if letra == '*' else [letra]}
        q['referencias_visuais'] = [p for p in q['paginas'] if p in visuais]
        if q['referencias_visuais']:
            q['pendencias'].append('Elementos visuais/vetoriais no corpo: conferir páginas do PDF original')
    return qs, visuais


def processar(captacoes, lote, saida, base):
    captacoes = Path(captacoes).resolve()
    entrega = cli([sys.executable, str(ROOT/'captador/app.py'), '--raiz', str(captacoes), 'entrega'], {'lote':lote})
    pacote = entrega['pacote']
    exigir(re.fullmatch(r'(?:tipo\s*)?1', pacote['identificacao']['caderno'].strip(), flags=re.I),
           'Neste perfil, selecionar caderno Tipo 1')
    exigir('ENAM' in pacote['identificacao']['prova'].upper(), 'Perfil implementado apenas para ENAM')
    caminhos = []
    for tipo in ('prova', 'gabarito'):
        d = pacote[tipo]
        path = (captacoes / pacote['raiz_originais'] / d['arquivo']).resolve()
        exigir(path.is_relative_to(captacoes), 'Original fora da pasta de captação')
        raw = path.read_bytes()
        exigir(raw.startswith(b'%PDF-') and hashlib.sha256(raw).hexdigest() == d['sha256'], 'PDF inválido ou corrompido')
        caminhos.append(path)
    exigir(pacote['identificacao']['ano'] == pacote['identificacao']['edicao'][:4], 'Ano e edição do lote divergem')
    qs, visuais = extrair(*caminhos, edicao=pacote['identificacao']['edicao'])
    descritores = cli([sys.executable, '-m', 'basequestoes', '--base', str(Path(base).resolve()), 'descrever-candidatos'], qs,
                      cwd=ROOT/'organizador')['abordagens']
    exigir(len(descritores) == len(qs), 'Quantidade de descritores diverge das questões')
    for q, perfil in zip(qs, descritores):
        q['abordagem'] = perfil
        if q['gabarito']['situacao'] != 'anulado':
            q['gabarito']['situacao'] = pacote['gabarito']['situacao_gabarito']
    pendencias = ['Descritores lexicais não confirmam tema ou conhecimento exigido semanticamente.']
    if visuais:
        pendencias.append('Elementos visuais/vetoriais pendentes de representação: páginas '+', '.join(map(str,visuais)))
    if pacote['complementos']:
        pendencias.append('Retificações/complementos recebidos ainda não interpretados automaticamente')
    resultado = {'versao':1,'extrator':'enam_fgv/1','encaminhamento':entrega['id'], 'protocolo':pacote['protocolo'],
                 'identificacao':pacote['identificacao'], 'documentos':pacote,
                 'estado':'extraido_com_pendencias', 'pendencias':pendencias,
                 'contagens':{'questoes':len(qs),'assertivas':sum(len(q['assertivas']) for q in qs),
                              'anuladas':[q['numero_original'] for q in qs if q['gabarito']['situacao']=='anulado']},
                 'dependencias':{n:importlib.metadata.version(n) for n in ('pdfplumber','pypdf')}, 'questoes':qs}
    # Verifica novamente a entrega atual para não publicar um resultado de lote alterado durante a extração.
    atual = cli([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(captacoes),'entrega'],
                {'lote':lote, 'encaminhamento':entrega['id']})
    exigir(atual['pacote'] == pacote, 'Lote mudou durante processamento; repetir')
    resultado['implementacao_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    id_ = hashlib.sha256(json.dumps(resultado,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    saida = Path(saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    destino = saida / (id_+'.json')
    fd, tmp = tempfile.mkstemp(dir=saida,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(resultado,f,ensure_ascii=False,indent=2)
            f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,destino)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    cli([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(captacoes),'registrar_extracao'],
        {'lote':lote,'encaminhamento':entrega['id'],'resultado_id':id_,
         'estado':resultado['estado'],'contagens':resultado['contagens']})
    return dict(resultado, resultado_id=id_)


def main():
    parser = argparse.ArgumentParser(description='Digitalizador ENAM/FGV local, sem IA')
    parser.add_argument('--captacoes', type=Path, default=ROOT/'captador/trabalho')
    parser.add_argument('--saida', type=Path, default=Path(__file__).parent/'trabalho')
    parser.add_argument('--base', type=Path, default=ROOT/'organizador')
    parser.add_argument('lote')
    args = parser.parse_args()
    try:
        print(json.dumps(processar(args.captacoes,args.lote,args.saida,args.base), ensure_ascii=False))
        return 0
    except Exception as exc:
        print('Erro: '+str(exc),file=sys.stderr)
        return 1


if __name__=='__main__': sys.exit(main())
