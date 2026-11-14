let tokenCaptacao='',captacaoCarregada=false;
const cap=id=>document.getElementById(id);
function capElemento(tag,texto){const e=document.createElement(tag);e.textContent=texto;return e;}
function canais(){cap('campo-upload').hidden=cap('canal-material').value!=='upload';cap('campo-pasta').hidden=cap('canal-material').value!=='pasta';cap('campo-situacao').hidden=cap('tipo-documento').value!=='gabarito';}
async function atualizarCaptacao(selecionado){
  const r=await fetch('/api/captacao');const d=await r.json();if(!r.ok)throw Error(d.erro);
  tokenCaptacao=d.token_captacao;const destino=cap('lote-destino'),anterior=selecionado||destino.value;destino.replaceChildren();
  cap('lista-lotes').replaceChildren();
  for(const lote of d.lotes){const i=lote.identificacao;const titulo=`${i.prova} · ${i.edicao} · ${i.caderno}${i.cargo?' · '+i.cargo:''}`;const o=capElemento('option',titulo+' · '+lote.id.slice(0,8));o.value=lote.id;destino.append(o);
    const a=document.createElement('article');a.append(capElemento('h3',titulo),capElemento('p',`Lote ${lote.id} — ${lote.estado==='pronto_para_digitalizador'?'Pronto para o Digitalizador':'Aguardando prova'}`));
    const ul=document.createElement('ul');for(const doc of lote.documentos)ul.append(capElemento('li',`${doc.tipo}${doc.situacao_gabarito?' ('+doc.situacao_gabarito+')':''}: ${doc.nome_original} — SHA-256 ${doc.sha256}`));a.append(ul);
    for(const p of lote.pendencias)a.append(capElemento('p','Pendente: '+p));
    a.append(capElemento('p','Digitalização não iniciada. O processamento de PDF ainda será implementado.'));cap('lista-lotes').append(a);
  }
  if([...destino.options].some(o=>o.value===anterior))destino.value=anterior;
  cap('arquivo-pasta').replaceChildren();for(const f of d.entrada){const o=capElemento('option',`${f.nome} (${f.tamanho} bytes)`);o.value=f.nome;cap('arquivo-pasta').append(o);}
  for(const erro of d.erros)cap('lista-lotes').append(capElemento('p',`Erro no lote ${erro.lote}: ${erro.erro}`));
  captacaoCarregada=true;return d;
}
async function postarCaptacao(acao,dados){const r=await fetch('/api/captacao/'+acao,{method:'POST',headers:{'Content-Type':'application/json','X-Captacao-Token':tokenCaptacao},body:JSON.stringify(dados)});const d=await r.json();if(!r.ok)throw Error(d.erro);return d;}
async function executarCaptacao(form,tarefa){const botao=form.querySelector('button');botao.disabled=true;cap('aviso-captacao').textContent='Recebendo material…';try{await tarefa();}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;}finally{botao.disabled=false;}}
cap('aba-consulta').onclick=()=>{cap('area-consulta').hidden=false;cap('area-captacao').hidden=true;};
cap('aba-captacao').onclick=async()=>{cap('area-consulta').hidden=true;cap('area-captacao').hidden=false;if(!captacaoCarregada){try{await atualizarCaptacao();}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;}}};
cap('criar-lote').onsubmit=e=>{e.preventDefault();executarCaptacao(e.currentTarget,async()=>{const d=await postarCaptacao('criar',Object.fromEntries(new FormData(cap('criar-lote'))));await atualizarCaptacao(d.id);cap('aviso-captacao').textContent='Lote criado. Adicione o documento de questões.';});};
cap('anexar-material').onsubmit=e=>{e.preventDefault();executarCaptacao(e.currentTarget,async()=>{
  const dados=Object.fromEntries(new FormData(cap('anexar-material')));if(!dados.lote)throw Error('Crie ou selecione um lote.');if(dados.tipo!=='gabarito')dados.situacao_gabarito='';
  if(cap('canal-material').value==='pasta'){dados.nome=cap('arquivo-pasta').value;dados.entrada=dados.nome;if(!dados.nome)throw Error('Nenhum arquivo selecionado na pasta.');}
  else{const f=cap('arquivo-material').files[0];if(!f)throw Error('Selecione um arquivo.');if(f.size>15*1024*1024)throw Error('O limite é 15 MiB por arquivo.');dados.nome=f.name;dados.conteudo_base64=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onerror=()=>reject(Error('Falha na leitura do arquivo'));reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(f);});}
  const d=await postarCaptacao('anexar',dados);cap('arquivo-material').value='';await atualizarCaptacao(d.id);cap('aviso-captacao').textContent='Documento recebido. Original e vínculo registrados.';
});};
cap('verificar-entrada').onclick=async()=>{try{const d=await atualizarCaptacao();cap('aviso-captacao').textContent=`${d.entrada.length} arquivo(s) na entrada; ${d.lotes.length} lote(s).`;}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;}};
cap('tipo-documento').onchange=canais;cap('canal-material').onchange=canais;canais();
