"""Reserva pares de originais por URL ou convenção explícita *_cad.pdf/*_gab.pdf."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from app import LIMITE, gravar, exigir, agora
from rede import descobrir, obter

# Conteúdo conferido contra o gabarito definitivo oficial da FGV, não pelo nome da URL.
GABARITOS_CONHECIDOS = {
    '81c1cbfbcab8df8d6ba0cd2f1ac2950b16cefe6147ed6490af8799b14dbfbba7': {
        'situacao':'definitivo','edicao':'2026.1',
        'fonte':'https://conhecimento.fgv.br/sites/default/files/concursos/enam-exame-nacional-de-magistratura-2026.1.pdf'}
}


def identidade(titulo):
    if 'enam' not in titulo.casefold():
        return {}
    edicoes = re.findall(r'(20[0-9]{2})[._-]([12])(?:\D|$)',titulo)
    if not edicoes:
        return {}
    ano, semestre = edicoes[-1]
    return {'prova':'Exame Nacional da Magistratura (ENAM)','edicao':ano+'.'+semestre,
            'caderno':'Tipo 1','orgao':'ENFAM','cargo':'Habilitação à magistratura (ENAM)',
            'banca':'FGV','ano':ano,'fonte':'PDF ENAM/FGV',
            'identificacao_proposta':True}


def reservar(c, titulo, fontes, canal):
    # URLs são a identidade da reserva; para pastas, usa nomes e hashes dos arquivos.
    for fonte in fontes.values():
        if canal != 'url':
            exigir(not fonte.is_symlink() and fonte.stat().st_size <= LIMITE, 'Arquivo de entrada inválido ou acima de 15 MiB')
    chave = {k:(v if canal == 'url' else {'nome':v.name,'sha256':hashlib.sha256(v.read_bytes()).hexdigest()}) for k,v in fontes.items()}
    id_ = hashlib.sha256(json.dumps(chave,sort_keys=True).encode()).hexdigest()
    pasta = c.raiz/'reservados'/id_
    exigir(pasta.resolve().is_relative_to(c.raiz), 'Reserva fora da captação')
    pasta.mkdir(parents=True,exist_ok=True)
    path = pasta/'registro.json'
    if path.exists():
        r = json.loads(path.read_text(encoding='utf-8'))
    else:
        r = {'versao':1,'id':id_,'titulo':titulo,'canal':canal,'recebido_em':agora(),
             'identificacao_sugerida':identidade(titulo),'documentos':{},'erros':{}}
    for tipo,fonte in fontes.items():
        if tipo in r['documentos']:
            d = r['documentos'][tipo]
            exigir(hashlib.sha256((pasta/d['arquivo']).read_bytes()).hexdigest() == d['sha256'], 'Reserva corrompida')
            continue
        try:
            if canal == 'url':
                raw,download = obter(fonte)
                nome = Path(urlsplit(fonte).path).name
            else:
                exigir(not fonte.is_symlink() and fonte.stat().st_size <= LIMITE, 'Arquivo de entrada inválido')
                raw,download,nome = fonte.read_bytes(),None,fonte.name
            exigir(raw.startswith(b'%PDF-') and 0 < len(raw) <= LIMITE, 'Conteúdo não é PDF válido ou excede 15 MiB')
            arquivo = 'conteudo_'+('cad' if tipo=='prova' else 'gab')+'.pdf'
            sha = hashlib.sha256(raw).hexdigest()
            # Nunca modificar o original; publicação atômica na reserva.
            import os, tempfile
            fd,tmp = tempfile.mkstemp(dir=pasta,suffix='.tmp')
            try:
                with os.fdopen(fd,'wb') as f:
                    f.write(raw); f.flush(); os.fsync(f.fileno())
                os.replace(tmp,pasta/arquivo)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
            d = {'arquivo':arquivo,'nome_original':nome,'sha256':sha,'tamanho':len(raw),
                 'url_origem':fonte if canal=='url' else ''}
            if download:
                d['download'] = download
            r['documentos'][tipo] = d
            r['erros'].pop(tipo,None)
        except (ValueError,OSError) as exc:
            r['erros'][tipo] = str(exc)
        gravar(path,r)
    r['estado'] = 'par_reservado' if set(r['documentos']) == {'prova','gabarito'} else 'aguardando_par'
    gravar(path,r)
    return r


def receber(c, dados):
    resultados, erros = [], []
    def receber_par(titulo,fontes,canal):
        try:
            reserva=reservar(c,titulo,fontes,canal)
            if not any(r['id']==reserva['id'] for r in resultados):
                resultados.append(reserva)
        except (ValueError,OSError,KeyError,TypeError) as exc:
            erros.append({'titulo':titulo,'erro':str(exc)})
    with c.bloqueio():
        urls = dados.get('urls',[])
        exigir(isinstance(urls,list) and len(urls)<=50 and all(isinstance(u,str) for u in urls), 'Informar até 50 URLs')
        if dados.get('prova_url') or dados.get('gabarito_url'):
            fontes = {k:dados[k+'_url'] for k in ('prova','gabarito') if dados.get(k+'_url')}
            receber_par(dados.get('titulo','PDF recebido'),fontes,'url')
        grupos, paginas = {}, []
        for url in urls:
            u = urlsplit(url)
            qc = re.fullmatch(r'/prova/arquivo_(prova|gabarito)/([0-9]+)/[^/]+',u.path) if u.hostname == 'arquivos.qconcursos.com' else None
            par = re.fullmatch(r'(.+)_(cad|gab)\.pdf',Path(u.path).name,re.I)
            if qc or par:
                chave = ('qc',qc[2]) if qc else (u.netloc,str(Path(u.path).parent),par[1])
                tipo = qc[1] if qc else ('prova' if par[2].lower()=='cad' else 'gabarito')
                grupo = grupos.setdefault(chave,{})
                exigir(tipo not in grupo or grupo[tipo] == url, 'Mais de uma URL para o mesmo papel no par')
                grupo[tipo] = url
            else:
                paginas.append(url)
        for fontes in grupos.values():
            titulo = Path(urlsplit(fontes.get('prova') or fontes['gabarito']).path).name
            receber_par(titulo,fontes,'url')
        for url in paginas:
            try:
                d = descobrir(url)
                if d['pdf_direto']:
                    receber_par(Path(urlsplit(url).path).name,{'prova':url},'url')
                else:
                    exigir(d['candidatos'],'Nenhum link rotulado de prova/gabarito encontrado')
                    for candidato in d['candidatos']:
                        fontes = {k:candidato[k+'_url'] for k in ('prova','gabarito') if candidato.get(k+'_url')}
                        receber_par(candidato['titulo'],fontes,'url')
            except (ValueError,OSError) as exc:
                erros.append({'url':url,'erro':str(exc)})
        if dados.get('pasta'):
            pasta = Path(dados['pasta']).resolve()
            exigir(pasta.is_dir(),'Pasta de entrada não encontrada')
            pares = {}
            for p in sorted(pasta.iterdir()):
                if not p.is_file() or p.is_symlink():
                    continue
                m = re.fullmatch(r'(.+)_(cad|gab)\.pdf',p.name,re.I)
                if m:
                    par = pares.setdefault(m.group(1),{})
                    tipo = 'prova' if m.group(2).lower() == 'cad' else 'gabarito'
                    exigir(tipo not in par,'Nomes ambíguos para o mesmo par')
                    par[tipo] = p
            for titulo,fontes in pares.items():
                receber_par(titulo,fontes,'pasta')
    return {'reservas':resultados,'erros':erros,'escopo':'links da página informada; sem percorrer outras páginas'}


def preparar(c, dados):
    id_ = dados.get('reserva')
    exigir(isinstance(id_,str) and re.fullmatch('[a-f0-9]{64}',id_), 'Reserva inválida')
    path = c.raiz/'reservados'/id_/'registro.json'
    exigir(path.resolve().is_relative_to(c.raiz), 'Reserva fora da captação')
    r = json.loads(path.read_text(encoding='utf-8'))
    exigir(set(r['documentos']) == {'prova','gabarito'}, 'Reserva incompleta: exige caderno e gabarito')
    ident = dados['identificacao']
    gab = r['documentos']['gabarito']
    conhecido = GABARITOS_CONHECIDOS.get(gab['sha256'])
    situacao = dados.get('situacao_gabarito')
    if conhecido:
        exigir(ident['edicao'] == conhecido['edicao'], 'Gabarito conhecido pertence a outra edição')
        situacao = situacao or conhecido['situacao']
    exigir(situacao in ('preliminar','definitivo'), 'Declarar situacao_gabarito; nome de arquivo não comprova que é definitivo')
    estado = c.estado()
    exigir(not estado['erros'],'Há lotes corrompidos no Captador')
    # Retoma lotes interrompidos, sem reutilizar outro caderno ou outra edição.
    lote = next((m for m in estado['lotes'] if m['versao']==2 and all(m['identificacao'].get(k)==ident.get(k,'')
                for k in ('orgao_id','cargo_id','prova','banca','ano','edicao','caderno','etapa'))),None)
    lote = lote or c.criar(ident)
    for tipo in ('prova','gabarito'):
        antigos = [d for d in lote['documentos'] if d['tipo']==tipo]
        esperado = r['documentos'][tipo]
        if antigos:
            exigir(len(antigos)==1 and antigos[0]['sha256']==esperado['sha256'], 'Lote existente contém outro arquivo; usar captação explícita para retificações')
            if tipo == 'gabarito':
                exigir(antigos[0]['situacao_gabarito']==situacao,'Situação do gabarito diverge do lote existente')
            continue
        lote = c.anexar({'lote':lote['id'],'tipo':tipo,'nome':esperado['nome_original'],
                        'reserva':id_,'situacao_gabarito':situacao if tipo=='gabarito' else ''})
    encaminhamento = c.encaminhar({'lote':lote['id'],'gabarito_sha256':gab['sha256']})
    return {'lote':lote['id'],'protocolo':lote['protocolo'],'encaminhamento':encaminhamento['id']}
