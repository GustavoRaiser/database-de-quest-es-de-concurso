"""Indícios lexicais explicáveis, sem inferência semântica ou chamadas de rede."""
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
import math
import re
import unicodedata

CAMPOS = ('conteudo','recorte','raciocinio','estrutura_redacao')
STOP = set('a o as os um uma uns umas de da do das dos em no na nos nas ao aos e ou que se por para com como qual quais assinale alternativa alternativas correta corretas incorreta incorretas questao questoes acerca sobre segundo seguinte seguintes caso nesse nesta deste dessa esse essa isto sua seu seus suas foi ser sao esta estao dos das pelo pela pelos pelas'.split())
INDETERMINADOS = {'indeterminado','nao identificado','outro',''}


def canon(valor):
    return json.dumps(valor,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n'


def digest(valor):
    return hashlib.sha256(canon(valor).encode()).hexdigest()


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD',texto.casefold()) if not unicodedata.combining(c))


def tokens(texto):
    return re.findall(r'[a-z0-9]+',normalizar(texto))


def texto_perfil(perfil,campo,declarado):
    t=perfil.get(campo,'')
    if not declarado or normalizar(t).strip(' .') in INDETERMINADOS or normalizar(t).startswith(('nao identificado','nao determinado')):
        return Counter()
    return Counter(p for p in tokens(t) if p not in STOP)


def shingles(seq,n=2):
    if len(seq)<n:
        return set(seq)
    return {' '.join(seq[i:i+n]) for i in range(len(seq)-n+1)}


def jaccard(a,b):
    return len(a&b)/len(a|b) if a or b else None


def vetores(contadores):
    df=Counter(t for contador in contadores for t in contador)
    n=len(contadores)
    resultado=[]
    for contador in contadores:
        v={t:(1+math.log(c))*(1+math.log((1+n)/(1+df[t]))) for t,c in contador.items()}
        norma=math.sqrt(sum(x*x for x in v.values()))
        resultado.append({t:x/norma for t,x in v.items()} if norma else {})
    return resultado,df


def cos(a,b):
    if not a or not b:
        return None
    if len(a)>len(b):a,b=b,a
    return min(1.0,max(0.0,sum(v*b.get(k,0) for k,v in a.items())))


def validar_config(c):
    if not isinstance(c,dict) or c.get('versao')!=1 or not isinstance(c.get('pesos'),dict) or set(c['pesos'])!=set(CAMPOS):
        raise ValueError('Critérios/versão incompatíveis')
    for valor in c['pesos'].values():
        if type(valor) not in (int,float) or not math.isfinite(valor) or valor<=0:
            raise ValueError('Pesos devem ser positivos e finitos')
    if abs(sum(c['pesos'].values())-1)>1e-9:raise ValueError('Pesos devem somar 1')
    for campo in ('max_postagem','termos_busca','vizinhos'):
        if type(c.get(campo)) is not int or c[campo]<1:raise ValueError(campo+' deve ser inteiro positivo')
    for campo in ('limiar','limiar_grupo','cobertura_minima'):
        if type(c.get(campo)) not in (int,float) or not math.isfinite(c[campo]):raise ValueError(campo+' deve ser número finito')
    if not (0<=c['limiar']<=c['limiar_grupo']<=100):raise ValueError('Limiares: 0 <= limiar <= limiar_grupo <= 100')
    if not (0<c['cobertura_minima']<=1):raise ValueError('Cobertura deve estar entre 0 e 1')


class Motor:
    def __init__(self,snapshot,config):
        validar_config(config)
        self.config=config
        self.itens=sorted(snapshot['itens'],key=lambda x:x['id'])
        self.ids={q['id']:i for i,q in enumerate(self.itens)}
        if len(self.ids)!=len(self.itens):raise ValueError('IDs repetidos no snapshot')
        self.docs=[]
        for item in self.itens:
            q=item['questao'];m=item.get('metadados') or {};perfil=m.get('abordagem') or {}
            textos=[q[1],*q[2],*m.get('textos_apoio',[])]
            seqs=[tokens(t) for t in textos]
            seq=[t for s in seqs for t in s]
            relevantes=[t for t in seq if t not in STOP and (len(t)>2 or t.isdigit())]
            conceitos=[v for v in perfil.get('conceitos',[]) if normalizar(v) not in INDETERMINADOS]
            declarado=perfil.get('estado')=='declarada' and perfil.get('geracao') in ('humano','ia') and not perfil.get('pendencias')
            razao=perfil.get('raciocinio','indeterminado')
            if normalizar(razao) in INDETERMINADOS:razao=None
            self.docs.append({'seqs':seqs,'termos':Counter(relevantes),
                'frases':Counter(p for s in seqs for p in sorted(shingles(s))),
                'redacao':{('enunciado',0):shingles(tokens(q[1]),3),
                           **{('assertiva',i):shingles(tokens(t),3) for i,t in enumerate(q[2])},
                           **{('apoio',i):shingles(tokens(t),3) for i,t in enumerate(m.get('textos_apoio',[]))}},
                'conceitos':conceitos,'raciocinio':razao,
                'conteudo_declarado':texto_perfil(perfil,'conteudo_exigido',declarado),
                'recorte_declarado':texto_perfil(perfil,'recorte_especifico',declarado),
                'igualdade':digest(seqs),'perfil':perfil,'visuais':bool(m.get('recursos')),
                'polaridade':sorted(set(tokens(q[1])) & {'nao','exceto','incorreta','incorretas','vedado'})})
        self.v,self.df=vetores([d['termos'] for d in self.docs])
        self.f,_=vetores([d['frases'] for d in self.docs])
        self.conteudos,_=vetores([d['conteudo_declarado'] for d in self.docs])
        self.recortes,_=vetores([d['recorte_declarado'] for d in self.docs])
        self.postagens=defaultdict(list);self.iguais=defaultdict(list)
        self.post_conceitos=defaultdict(list)
        for i,v in enumerate(self.v):
            for termo in v:
                if self.df[termo]<=config['max_postagem']:self.postagens[termo].append(i)
            self.iguais[self.docs[i]['igualdade']].append(i)
            for conceito in {normalizar(x) for x in self.docs[i]['conceitos']}:
                self.post_conceitos[conceito].append(i)

    def candidatas(self,i):
        c=self.config;v=self.v[i];pontuacao=defaultdict(float)
        termos=sorted((t for t in v if t in self.postagens),key=lambda t:(-v[t],t))[:c['termos_busca']]
        for termo in termos:
            for j in self.postagens[termo]:
                if j!=i:pontuacao[j]+=v[termo]*self.v[j][termo]
        for conceito in {normalizar(x) for x in self.docs[i]['conceitos']}:
            postagem=self.post_conceitos[conceito]
            if len(postagem)<=c['max_postagem']:
                for j in postagem:
                    if j!=i:pontuacao[j]+=0.25
        # O balde de texto igual continua útil mesmo quando todos os termos são comuns.
        for j in self.iguais[self.docs[i]['igualdade']]:
            if j!=i:pontuacao[j]=max(1.0,pontuacao[j])
        ordem=sorted(pontuacao,key=lambda j:(-pontuacao[j],self.itens[j]['id']))
        return ordem[:c['vizinhos']],len(ordem)>c['vizinhos']

    def comparar(self,i,j):
        if i==j:raise ValueError('Selecionar duas questões diferentes')
        if self.itens[i]['id']>self.itens[j]['id']:i,j=j,i
        a,b=self.docs[i],self.docs[j]
        metricas={'conteudo':cos(self.v[i],self.v[j]),'recorte':cos(self.f[i],self.f[j]),
                  'raciocinio':None if not a['raciocinio'] or not b['raciocinio'] else float(a['raciocinio']==b['raciocinio'])}
        conceitos=jaccard({normalizar(x) for x in a['conceitos']},{normalizar(x) for x in b['conceitos']}) if a['conceitos'] and b['conceitos'] else None
        if conceitos is not None and metricas['conteudo'] is not None:
            metricas['conteudo']=0.75*metricas['conteudo']+0.25*conceitos
        declarado=cos(self.conteudos[i],self.conteudos[j])
        if declarado is not None:
            metricas['conteudo']=declarado if metricas['conteudo'] is None else (declarado+metricas['conteudo'])/2
        recorte=cos(self.recortes[i],self.recortes[j])
        if recorte is not None:metricas['recorte']=recorte
        # Enunciado e alternativas em sua ordem. Apoios também participam da comparação textual.
        campos=sorted(a['redacao'].keys() | b['redacao'].keys())
        redacoes=[jaccard(a['redacao'].get(k,set()),b['redacao'].get(k,set())) for k in campos]
        redacoes=[v for v in redacoes if v is not None]
        metricas['estrutura_redacao']=(sum(redacoes)/len(campos) if redacoes else None)
        cobertura=sum(self.config['pesos'][k] for k,v in metricas.items() if v is not None)
        score=100*sum(self.config['pesos'][k]*v for k,v in metricas.items() if v is not None)/cobertura if cobertura else 0
        avisos=['Semelhança lexical não confirma que as questões exigem o mesmo conhecimento.']
        if a['visuais'] or b['visuais']:avisos.append('Recursos visuais não interpretados; conferir os originais.')
        if a['polaridade']!=b['polaridade']:avisos.append('Marcadores de negação/exceção diferentes no enunciado.')
        if any(d['perfil'].get('pendencias') or d['perfil'].get('estado')=='proposta' for d in (a,b)):
            avisos.append('Há perfis propostos ou com pendências; não são confirmação semântica.')
        termos=sorted(self.v[i].keys() & self.v[j].keys(),key=lambda t:(-self.v[i][t]*self.v[j][t],t))[:8]
        frases=sorted(self.f[i].keys() & self.f[j].keys(),key=lambda t:(-self.f[i][t]*self.f[j][t],t))[:8]
        return {'a':self.itens[i]['id'],'b':self.itens[j]['id'],'score':round(score,4),
            'cobertura':round(cobertura,6),'dimensoes':{k:None if v is None else round(100*v,4) for k,v in metricas.items()},
            'estado':'proposta_lexical','evidencias':{'termos_comuns':termos,'expressoes_comuns':frases,
                'conceitos_comuns':sorted(x for x in set(a['conceitos']) if normalizar(x) in {normalizar(y) for y in b['conceitos']}),
                'raciocinio_a':a['raciocinio'],'raciocinio_b':b['raciocinio']},
            'fontes_dimensoes':{'conteudo':'texto e conceitos; perfil declarado' if declarado is not None else 'texto e conceitos propostos',
                               'recorte':'perfil declarado' if recorte is not None else 'expressões do texto',
                               'raciocinio':'rótulos dos perfis' if metricas['raciocinio'] is not None else 'ausente',
                               'estrutura_redacao':'trigramas em enunciado, alternativas e apoios na ordem'},'avisos':avisos}

    def indice(self,id_):
        if id_ not in self.ids:raise ValueError('Questão não encontrada no recorte: '+id_)
        return self.ids[id_]

    def analisar(self,exaustivo=False):
        n=len(self.itens);candidatos=set();truncados=[]
        if exaustivo:
            candidatos=set(combinations(range(n),2))
        else:
            for i in range(n):
                vizinhos,truncado=self.candidatas(i)
                if truncado:truncados.append(self.itens[i]['id'])
                candidatos.update(tuple(sorted((i,j))) for j in vizinhos)
        comparacoes=[self.comparar(i,j) for i,j in sorted(candidatos)]
        # Pares nunca calculados não viram similaridade zero nem equivalência indireta.
        pares=[p for p in comparacoes if p['score']>=self.config['limiar'] and p['cobertura']>=self.config['cobertura_minima']]
        fortes={(p['a'],p['b']):p['score'] for p in pares if p['score']>=self.config['limiar_grupo']}
        conjuntos={q['id']:{q['id']} for q in self.itens}
        for p in sorted(pares,key=lambda p:(-p['score'],p['a'],p['b'])):
            a,b=conjuntos[p['a']],conjuntos[p['b']]
            if a is b:continue
            if all(tuple(sorted((x,y))) in fortes for x in a for y in b):
                novo=a|b
                for id_ in novo:conjuntos[id_]=novo
        grupos=[];vistos=set()
        for grupo in conjuntos.values():
            membros=tuple(sorted(grupo))
            if len(membros)<2 or membros in vistos:continue
            vistos.add(membros)
            grupos.append({'id':digest(membros),'questoes':list(membros),'estado':'proposta_lexical',
                           'score_minimo':min(fortes[tuple(sorted(par))] for par in combinations(membros,2))})
        pares.sort(key=lambda p:(-p['score'],p['a'],p['b']))
        vizinhos={q['id']:[] for q in self.itens}
        for indice,p in enumerate(pares):
            vizinhos[p['a']].append(indice);vizinhos[p['b']].append(indice)
        nos=[]
        for item,d in zip(self.itens,self.docs):
            origens=(item.get('metadados') or {}).get('origens',[])
            nos.append({'id':item['id'],'conteudo_sha256':digest(item),'situacao':item['questao'][0],
                'conceitos_propostos':d['conceitos'],
                'ocorrencias':[{k:o[k] for k in ('ficha_prova','numero_original','pagina','paginas','url','id_externo','coletado_em') if k in o} for o in origens]})
        return {'nos':nos,'pares':pares,'grupos':sorted(grupos,key=lambda g:g['questoes']), 'vizinhos':vizinhos,
                'diagnostico':{'questoes':n,'pares_possiveis':n*(n-1)//2,'pares_comparados':len(candidatos),
                    'pares_nao_comparados':n*(n-1)//2-len(candidatos),'pares_retidos':len(pares),
                    'grupos':len(grupos),'buscas_truncadas':truncados,'modo':'exaustivo' if exaustivo else 'indice_invertido',
                    'termos_muito_comuns_omitidos':sum(df>self.config['max_postagem'] for df in self.df.values())}}
