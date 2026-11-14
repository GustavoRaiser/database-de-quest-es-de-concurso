const campos=['orgao','cargo','disciplina','tema'];
const grupos=['orgaos','cargos','disciplinas','temas'];
const $=id=>document.getElementById(id);
let pagina=1, paginas=0, requisicao=0;
function elemento(tag,texto,classe){const e=document.createElement(tag);if(texto!==undefined)e.textContent=texto;if(classe)e.className=classe;return e;}
async function buscar(url){const r=await fetch(url);const d=await r.json();if(!r.ok)throw new Error(d.erro||'Falha na consulta');return d;}
function recursos(alvo,lista,posicao,indice){
  for(const r of lista.filter(r=>r.posicao===posicao&&(indice===undefined||r.indice===indice)).sort((a,b)=>a.ordem-b.ordem)){
    if(!/^recursos\/[a-f0-9]{2}\/[a-f0-9]{64}$/.test(r.arquivo))continue;
    if(['image/png','image/jpeg','image/gif'].includes(r.tipo_mime)){
      const img=document.createElement('img');img.src='/'+r.arquivo;img.alt=r.descricao||'Imagem da questão';img.loading='lazy';alvo.append(img);
    }else{const link=elemento('a',r.descricao||'Baixar recurso associado');link.href='/'+r.arquivo;link.download='';alvo.append(link,document.createElement('br'));}
  }
}
function mostrar(item){
  const a=elemento('article'),m=item.metadados||{},rs=m.recursos||[];
  a.append(elemento('h2',item.id),elemento('span',['Atualizada','Desatualizada','Anulada'][item.questao[0]],'situacao'));
  a.append(elemento('p',campos.map(c=>item.classificacao[c].nome).join(' › ')));
  (m.textos_apoio||[]).forEach((t,i)=>{a.append(elemento('p',t,'texto'));recursos(a,rs,'texto_apoio',i+1);});
  recursos(a,rs,'antes_enunciado');a.append(elemento('p',item.questao[1],'texto'));recursos(a,rs,'apos_enunciado');
  const ol=elemento('ol');item.questao[2].forEach((t,i)=>{const li=elemento('li',t,'texto');recursos(li,rs,'assertiva',i+1);ol.append(li);});a.append(ol);
  if(m.gabarito){const d=elemento('details');d.append(elemento('summary','Ver gabarito'),elemento('p',`Situação: ${m.gabarito.situacao}. Posições corretas: ${m.gabarito.alternativas_corretas.join(', ')||'não informadas'}.`));a.append(d);}
  if(item.metadados){const d=elemento('details');d.append(elemento('summary','Metadados e procedência'),elemento('pre',JSON.stringify(m,null,2)));recursos(d,rs,'original');a.append(d);}
  return a;
}
async function carregar(){
  const atual=++requisicao;const p=new URLSearchParams({pagina,por_pagina:$('tamanho').value});campos.forEach(c=>{if($(c).value)p.set(c,$(c).value);});
  $('aviso').textContent='Consultando questões…';$('anterior').disabled=true;$('proxima').disabled=true;
  try{const d=await buscar('/api/questoes?'+p);if(atual!==requisicao)return;paginas=d.paginas;$('questoes').replaceChildren(...d.itens.map(mostrar));$('aviso').textContent=d.total?`${d.total} questão(ões) encontrada(s).`:'Nenhuma questão encontrada. Limpe os filtros ou acrescente questões à base.';$('pagina').textContent=paginas?`Página ${pagina} de ${paginas}`:'Sem resultados';$('anterior').disabled=pagina<=1;$('proxima').disabled=pagina>=paginas;}
  catch(e){if(atual!==requisicao)return;$('questoes').replaceChildren();$('aviso').textContent='Erro: '+e.message;$('pagina').textContent='';}
}
$('filtros').onsubmit=e=>{e.preventDefault();pagina=1;carregar();};
$('limpar').onclick=()=>{campos.forEach(c=>$(c).value='');pagina=1;carregar();};
$('tamanho').onchange=()=>{pagina=1;carregar();};
$('anterior').onclick=()=>{if(pagina>1){pagina--;carregar();}};
$('proxima').onclick=()=>{if(pagina<paginas){pagina++;carregar();}};
(async()=>{try{const c=await buscar('/api/catalogos');campos.forEach((campo,i)=>{for(const [id,nome]of Object.entries(c[grupos[i]])){const nomes=id.split('.').map((_,n)=>c[grupos[n]][id.split('.').slice(0,n+1).join('.')]);const o=elemento('option',nomes.join(' › '));o.value=id;$(campo).append(o);}});await carregar();}catch(e){$('aviso').textContent='Erro: '+e.message;}})();
