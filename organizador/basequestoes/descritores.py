"""Descritores lexicais explicáveis. Não interpretam o conhecimento necessário."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .abordagem import digest, validar
from .core import exigir, texto


def normalizar(t):
    return ''.join(c for c in unicodedata.normalize('NFD', t.casefold()) if not unicodedata.combining(c))


def descrever(candidato):
    exigir(isinstance(candidato, dict) and texto(candidato.get('enunciado')),
           'Candidato precisa de enunciado textual não vazio')
    for campo in ('assertivas','textos_apoio'):
        exigir(isinstance(candidato.get(campo, []), list) and all(isinstance(t,str) for t in candidato.get(campo, [])), campo+' deve ser lista de textos')
    q = [0, candidato['enunciado'], candidato.get('assertivas', [])]
    m = {'textos_apoio':candidato.get('textos_apoio',[]), 'recursos':candidato.get('recursos',[])}
    raw = Path(__file__).with_name('regras.json').read_bytes()
    regras = json.loads(raw)
    fontes = [('enunciado',None,q[1])]
    fontes += [('assertiva',i,t) for i,t in enumerate(q[2],1)]
    fontes += [('texto_apoio',i,t) for i,t in enumerate(m['textos_apoio'],1)]
    achados, evidencias = [], []
    for regra in regras['conceitos']:
        for campo,i,t in fontes:
            if any(re.search(r'(?<!\w)'+re.escape(normalizar(termo))+r'(?!\w)',normalizar(t)) for termo in regra['termos']):
                achados.append(regra)
                e = {'campo':campo, 'trecho':t}
                if i is not None:
                    e['indice']=i
                if e not in evidencias:
                    evidencias.append(e)
                break
    conceitos = [r['nome'] for r in achados] or ['Não identificado']
    comando = next((linha for linha in q[1].splitlines() if re.search(r'assinale|julgue|avalie|identifique|calcule',normalizar(linha))), '')
    raciocinio = ('calcular' if 'calcule' in normalizar(comando) else
                  'identificar_excecao' if 'exceto' in normalizar(comando) else 'indeterminado')
    p = {'versao_criterio':1,'base_sha256':digest(q,m), 'sintese':
         'Conceitos textualmente identificados: '+', '.join(conceitos)+'.' if achados else 'Não identificado pelas regras cadastradas.',
         'conteudo_exigido':'Não determinado semanticamente; ocorrências lexicais: '+', '.join(conceitos),
         'recorte_especifico':comando or 'Não identificado por regra de comando.',
         'conceitos':conceitos,'raciocinio':raciocinio,
         'estrutura':f'Enunciado com {len(q[1])} caracteres e {len(q[2])} assertivas em ordem original.',
         'evidencias':evidencias or [{'campo':'enunciado','trecho':q[1]}],
         'geracao':'regras','autor':'organizador/descritores','estado':'proposta',
         'pendencias':['Ocorrência textual não comprova o conhecimento exigido; classificação semântica não realizada.'],
         'regras_aplicadas':[r['id'] for r in achados], 'versao_regras':regras['versao'],
         'regras_sha256':hashlib.sha256(raw).hexdigest()}
    if m['recursos']:
        p['pendencias'].append('Recursos visuais não interpretados pelo descritor lexical.')
    validar(p,q,m)
    return p
