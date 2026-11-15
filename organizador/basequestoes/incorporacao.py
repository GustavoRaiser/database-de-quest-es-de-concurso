"""Entrada pública de candidatos; o Organizador é o único escritor do acervo."""
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

from .core import atomico, caminho_metadados, caminho_tema, exigir, ler_json, registro, serializar, codigo
from .descritores import descrever
from .transacoes import executar

ROOT = Path(__file__).resolve().parents[2]
ALFABETO = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def normalizar(nome):
    return ' '.join(unicodedata.normalize('NFC', nome).casefold().split())


def base62(n):
    if n == 0:
        return '0'
    s = ''
    while n:
        n, r = divmod(n,62)
        s = ALFABETO[r]+s
    return s


def categoria(catalogos, grupo, nome, pai='', preferido=None):
    exigir(isinstance(nome,str) and nome.strip(), 'Nome de categoria obrigatório')
    mapa = catalogos[grupo]
    encontrados = [k for k,v in mapa.items() if k.rpartition('.')[0] == pai and normalizar(v) == normalizar(nome)]
    exigir(len(encontrados) <= 1, 'Nome ambíguo no catálogo: '+nome)
    if encontrados:
        exigir(preferido is None or encontrados[0].split('.')[-1] == preferido, 'Código diverge da categoria existente')
        return encontrados[0]
    if preferido is None:
        n = 0
        while (pai+'.' if pai else '')+base62(n) in mapa:
            n += 1
        preferido = base62(n)
    exigir(codigo(preferido), 'Código base 62 inválido')
    chave = (pai+'.' if pai else '')+preferido
    exigir(chave not in mapa, 'Código já reservado: '+chave)
    mapa[chave] = nome.strip()
    return chave


def reservar(raiz, entrada):
    def preparar(base):
        orgao = categoria(base.catalogos,'orgaos',entrada['orgao'],preferido=entrada.get('orgao_id'))
        cargo = categoria(base.catalogos,'cargos',entrada['cargo'],orgao,entrada.get('cargo_id'))
        atomico(base.local('catalogos.json'),serializar(base.catalogos).encode())
        return {'orgao_id':orgao, 'cargo_id':cargo.split('.')[-1]}
    return executar(raiz, preparar)


def entrega(captacoes, lote, encaminhamento):
    p = subprocess.run([sys.executable,str(ROOT/'captador/app.py'),'--raiz',str(captacoes),'entrega'],
                       input=json.dumps({'lote':lote,'encaminhamento':encaminhamento}),text=True,
                       encoding='utf-8',capture_output=True,timeout=60)
    exigir(p.returncode == 0, p.stderr.strip())
    return json.loads(p.stdout)['pacote']


def incorporar(raiz, entrada):
    arquivo = Path(entrada['resultado']).resolve()
    r = ler_json(arquivo)
    digest = hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    exigir(arquivo.name == digest+'.json', 'Hash do resultado divergente')
    exigir(r.get('versao') == 2 and r.get('extrator') == 'enam_fgv/2', 'Contrato de extração não suportado')
    exigir(r.get('bloqueios') == [], 'Extração contém bloqueios técnicos')
    exigir(isinstance(r.get('questoes'),list) and len(r['questoes']) == 80 and
           [q['numero_original'] for q in r['questoes']] == [str(i) for i in range(1,81)], 'Sequência incompleta de questões')
    situacao = entrada.get('situacao_inicial')
    exigir(type(situacao) is int and situacao in (0,1), 'Declarar situacao_inicial 0 ou 1; não inferida da data')
    captacoes = Path(entrada['captacoes']).resolve()
    pacote = entrega(captacoes,r['documentos']['lote'],r['encaminhamento'])
    exigir(pacote == r['documentos'] and r['identificacao'] == pacote['identificacao'] and r['protocolo'] == pacote['protocolo'], 'Resultado e entrega divergem')
    ident = r['identificacao']
    grupo = ident['orgao_id']+'.'+ident['cargo_id']
    # Deduplicação por documento no mesmo órgão/cargo, independente do lote/host.
    chave = pacote['prova']['sha256']
    ficha_path = f'provas/{ident["orgao_id"]}/{ident["cargo_id"]}/{chave}.json'

    def preparar(base):
        categoria(base.catalogos,'orgaos',ident['orgao'],preferido=ident['orgao_id'])
        categoria(base.catalogos,'cargos',ident['cargo'],ident['orgao_id'],ident['cargo_id'])
        anterior = base.local(ficha_path)
        if anterior.exists():
            ficha = ler_json(anterior)
            exigir(ficha['gabarito_sha256'] == pacote['gabarito']['sha256'], 'Prova já incorporada com outro gabarito; não duplicar nem sobrescrever respostas')
            return {'estado':'ja_incorporado','novas_questoes':0,'mapeamento':ficha['mapeamento'],'ficha_prova':ficha_path}

        def copiar(path, esperado, mime):
            conteudo = path.read_bytes()
            exigir(hashlib.sha256(conteudo).hexdigest() == esperado, 'Recurso de origem corrompido')
            d = {'arquivo':f'recursos/{esperado[:2]}/{esperado}','sha256':esperado,'tipo_mime':mime}
            alvo = base.local(d['arquivo'])
            if alvo.exists():
                exigir(alvo.read_bytes() == conteudo, 'Recurso existente corrompido')
            else:
                atomico(alvo,conteudo)
            return d

        documentos = []
        for tipo in ('prova','gabarito'):
            d = pacote[tipo]
            path = (captacoes/pacote['raiz_originais']/d['arquivo']).resolve()
            exigir(path.is_relative_to(captacoes), 'Original fora da captação')
            local = copiar(path,d['sha256'],'application/pdf')
            local.update(tipo=tipo, url=d.get('url_origem') or 'urn:sha256:'+d['sha256'])
            documentos.append(local)
        recursos = {}
        for q in r['questoes']:
            for d in q.get('recursos',[]):
                exigir(d.get('tipo_mime') == 'image/png', 'Formato de recurso não suportado na extração')
                path = (arquivo.parent/d['arquivo']).resolve()
                exigir(path.is_relative_to(arquivo.parent), 'Recurso fora da extração')
                local = copiar(path,d['sha256'],d['tipo_mime'])
                exigir(local['arquivo'] == d['arquivo'], 'Caminho de recurso divergente')
                recursos[d['sha256']] = local
        hoje = date.today().isoformat()
        atomico(base.local(ficha_path),serializar({'versao':1,'grupo':grupo,'protocolo':r['protocolo'],
            'identificacao':ident,'documentos':documentos,'prova_sha256':chave,
            'gabarito_sha256':pacote['gabarito']['sha256'],'mapeamento':[]}).encode())
        novos, mapas, mapeamento = {}, {}, []
        for q in r['questoes']:
            exigir(q.get('disciplina') and not q.get('bloqueios'), 'Questão sem disciplina ou com bloqueio')
            disciplina = categoria(base.catalogos,'disciplinas',q['disciplina'],grupo)
            tema = categoria(base.catalogos,'temas','Não classificado',disciplina)
            path = caminho_tema(tema,'dados')
            base.indice['temas'][tema] = path
            if tema not in novos:
                atual = base.local(path)
                antigos = atual.read_bytes() if atual.exists() else b''
                novos[tema] = [antigos, antigos.count(b'\n')]
                mapas[tema] = base.metadados(tema) if atual.exists() else {}
            numero = novos[tema][1]+1
            gab = deepcopy(q['gabarito'])
            if gab['situacao'] != 'anulado':
                exigir(gab['situacao'] == pacote['gabarito']['situacao_gabarito'], 'Situação de resposta diverge da fonte')
            valor = [2 if gab['situacao'] == 'anulado' else situacao,q['enunciado'],q['assertivas']]
            registro(valor)
            novos[tema][0] += serializar(valor).encode()
            novos[tema][1] = numero
            meta = {'origens':[{'fonte':ident.get('fonte') or 'PDF recebido','coletado_em':pacote['prova']['recebido_em'][:10],
                    'id_externo':chave+':'+q['numero_original'],'numero_original':q['numero_original'],
                    'ficha_prova':ficha_path,'documento':documentos[0],'pagina':q['paginas'][0],
                    'paginas':q['paginas']}], 'gabarito':gab,'rotulos_originais':q['rotulos_originais'],
                    'recursos':deepcopy(q.get('recursos',[])), 'textos_apoio':q.get('textos_apoio',[]),
                    'classificacao':{'estado':'pendente','criterio':'disciplina do cabeçalho; tema não inferido'},
                    'situacao_declarada':{'valor':situacao,'criterio':'politica de cadastro informada na execução'},
                    'avisos_extracao':q.get('pendencias',[])}
            meta['abordagem'] = descrever(dict(meta,enunciado=q['enunciado'],assertivas=q['assertivas']))
            mapas[tema][str(numero)] = meta
            mapeamento.append({'numero_original':q['numero_original'],'questao_id':tema+'.'+str(numero)})
        for tema,(conteudo,_) in novos.items():
            atomico(base.local(caminho_tema(tema,'dados')),conteudo)
            atomico(base.local(caminho_metadados(tema)),serializar(mapas[tema]).encode())
        atomico(base.local('catalogos.json'),serializar(base.catalogos).encode())
        atomico(base.local('indice.json'),serializar(base.indice).encode())
        ficha = ler_json(base.local(ficha_path))
        ficha['mapeamento'] = mapeamento
        ficha['resultado_id'] = digest
        atomico(base.local(ficha_path),serializar(ficha).encode())
        nome = 'pdf-'+hashlib.sha256((grupo+':'+chave).encode()).hexdigest()[:40]
        manifesto = {'id':nome,'fonte':grupo+':'+chave,'coletado_em':hoje,'versao_importador':'organizador/1','documentos':documentos}
        relatorio = {'mapeamento':mapeamento,'pendencias':[],'avisos':r['pendencias'],
                     'classificacao_tematica':'pendente; temas Não classificado'}
        fingerprint = base.lote(manifesto,relatorio)
        atomico(base.local(f'importacoes/{nome}/manifesto.json'),serializar(dict(manifesto,fingerprint=fingerprint)).encode())
        atomico(base.local(f'importacoes/{nome}/relatorio.json'),serializar(relatorio).encode())
        exigir(entrega(captacoes,pacote['lote'],r['encaminhamento']) == pacote, 'Captação mudou durante incorporação')
        return {'estado':'incorporado','novas_questoes':len(mapeamento),'mapeamento':mapeamento,'ficha_prova':ficha_path,
                'avisos':r['pendencias'],'classificacao_tematica':'pendente'}
    return executar(raiz, preparar)
