let tokenCaptacao='',captacaoCarregada=false;
const cap=id=>document.getElementById(id);
function capElemento(tag,texto){const e=document.createElement(tag);e.textContent=texto;return e;}
function canais(){cap('campo-upload').hidden=cap('canal-material').value!=='upload';cap('campo-pasta').hidden=cap('canal-material').value!=='pasta';cap('campo-situacao').hidden=cap('tipo-documento').value!=='gabarito';}
async function atualizarCaptacao(selecionado){
  const r=await fetch('/api/captacao');const d=await r.json();if(!r.ok)throw Error(d.erro);
  tokenCaptacao=d.token_captacao;const destino=cap('lote-destino'),anterior=selecionado||destino.value;destino.replaceChildren();
  for(const lote of d.lotes){const i=lote.identificacao;const o=capElemento('option',`${lote.protocolo||'Sem protocolo'} · ${i.prova} · ${i.edicao} · ${i.caderno}`);o.value=lote.id;destino.append(o);}
  registroCaptacao=d.lotes;prepararFiltrosRegistro();mostrarRegistro();
  if([...destino.options].some(o=>o.value===anterior))destino.value=anterior;
  cap('arquivo-pasta').replaceChildren();for(const f of d.entrada){const o=capElemento('option',`${f.nome} (${f.tamanho} bytes)`);o.value=f.nome;cap('arquivo-pasta').append(o);}
  for(const erro of d.erros)cap('lista-lotes').append(capElemento('p',`Erro no lote ${erro.lote}: ${erro.erro}`));
  captacaoCarregada=true;return d;
}
async function postarCaptacao(acao,dados){const r=await fetch('/api/captacao/'+acao,{method:'POST',headers:{'Content-Type':'application/json','X-Captacao-Token':tokenCaptacao},body:JSON.stringify(dados)});const d=await r.json();if(!r.ok)throw Error(d.erro);return d;}
async function executarCaptacao(form,tarefa){const botao=form.querySelector('button');botao.disabled=true;cap('aviso-captacao').textContent='Recebendo material…';try{await tarefa();}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;}finally{botao.disabled=false;}}
cap('aba-consulta').onclick=()=>{cap('area-consulta').hidden=false;cap('area-captacao').hidden=true;};
cap('aba-captacao').onclick=async()=>{cap('area-consulta').hidden=true;cap('area-captacao').hidden=false;if(!captacaoCarregada){try{await atualizarCaptacao();}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;}}};
cap('criar-lote').onsubmit=e=>{e.preventDefault();executarCaptacao(e.currentTarget,async()=>{const dados=Object.fromEntries(new FormData(cap('criar-lote')));const d=await postarCaptacao(dados.lote?'identificar':'criar',dados);cancelarIdentificacao();await atualizarCaptacao(d.id);cap('aviso-captacao').textContent=`Protocolo ${d.protocolo} registrado. Adicione prova e gabarito para liberar o encaminhamento.`;});};
cap('anexar-material').onsubmit=e=>{e.preventDefault();executarCaptacao(e.currentTarget,async()=>{
  const dados=Object.fromEntries(new FormData(cap('anexar-material')));if(!dados.lote)throw Error('Crie ou selecione um lote.');if(dados.tipo!=='gabarito')dados.situacao_gabarito='';
  if(cap('canal-material').value==='pasta'){dados.nome=cap('arquivo-pasta').value;dados.entrada=dados.nome;if(!dados.nome)throw Error('Nenhum arquivo selecionado na pasta.');}
  else{const f=cap('arquivo-material').files[0];if(!f)throw Error('Selecione um arquivo.');if(f.size>15*1024*1024)throw Error('O limite é 15 MiB por arquivo.');dados.nome=f.name;dados.conteudo_base64=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onerror=()=>reject(Error('Falha na leitura do arquivo'));reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(f);});}
  const d=await postarCaptacao('anexar',dados);cap('arquivo-material').value='';await atualizarCaptacao(d.id);cap('aviso-captacao').textContent='Documento recebido. Original e vínculo registrados.';
});};
cap('verificar-entrada').onclick=async()=>{try{const d=await atualizarCaptacao();cap('aviso-captacao').textContent=`${d.entrada.length} arquivo(s) na entrada; ${d.lotes.length} lote(s).`;}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;}};
cap('tipo-documento').onchange=canais;cap('canal-material').onchange=canais;canais();

let registroCaptacao=[];
const filtrosRegistro=[['orgao_id','Órgão'],['grupo','Cargo (órgão.cargo)'],['banca','Banca'],['ano','Ano'],['escolaridade','Escolaridade'],['area_atuacao','Área de atuação'],['area_formacao','Área de formação'],['uf','UF'],['esfera','Esfera'],['etapa','Etapa'],['estado','Documentação'],['processamento','Processamento']];
function valorRegistro(lote,campo){return String(lote[campo]||lote.identificacao[campo]||'');}
function prepararFiltrosRegistro(){
  for(const [campo,nome] of filtrosRegistro){let seletor=cap('reg-'+campo);if(!seletor){const label=capElemento('label',nome);seletor=document.createElement('select');seletor.id='reg-'+campo;label.append(seletor);cap('campos-filtros-protocolo').append(label);seletor.onchange=mostrarRegistro;}
    const anterior=seletor.value;seletor.replaceChildren(capElemento('option','Todos'));seletor.options[0].value='';for(const valor of [...new Set(registroCaptacao.map(l=>valorRegistro(l,campo)).filter(Boolean))].sort()){const o=capElemento('option',valor);o.value=valor;seletor.append(o);}if([...seletor.options].some(o=>o.value===anterior))seletor.value=anterior;
  }
}
function mostrarRegistro(){
  const busca=cap('busca-protocolo').value.toLocaleLowerCase();const lista=registroCaptacao.filter(l=>filtrosRegistro.every(([k])=>!cap('reg-'+k).value||valorRegistro(l,k)===cap('reg-'+k).value)&&((l.protocolo||'')+' '+JSON.stringify(l.identificacao)).toLocaleLowerCase().includes(busca));
  cap('lista-lotes').replaceChildren();cap('total-protocolos').textContent=`${lista.length} de ${registroCaptacao.length} prova(s) registrada(s).`;
  for(const lote of lista){const i=lote.identificacao,a=document.createElement('article');a.append(capElemento('h3',`${lote.protocolo||'Sem protocolo'} · ${i.prova} · ${i.edicao} · ${i.caderno}`),capElemento('p',`${i.orgao||''} › ${i.cargo||''} · ${i.banca||'Banca pendente'} · ${i.ano||'Ano pendente'}`),capElemento('p',`Documentação: ${lote.estado}. Processamento: ${lote.processamento}.`));
    const ul=document.createElement('ul');for(const d of lote.documentos)ul.append(capElemento('li',`${d.tipo}${d.situacao_gabarito?' ('+d.situacao_gabarito+')':''}: ${d.nome_original} — SHA-256 ${d.sha256}`));a.append(ul);
    for(const p of lote.pendencias)a.append(capElemento('p','Pendente: '+p));
    if(lote.versao===1){const b=capElemento('button','Identificar lote antigo');b.type='button';b.onclick=()=>{const form=cap('criar-lote');for(const [k,v]of Object.entries(i)){if(form.elements.namedItem(k))form.elements.namedItem(k).value=v;}cap('identificar-legado').value=lote.id;cap('salvar-protocolo').textContent='Salvar identificação do lote';cap('cancelar-identificacao').hidden=false;form.scrollIntoView();};a.append(b);}
    const g=document.createElement('select');g.setAttribute('aria-label','Gabarito a encaminhar');for(const d of lote.documentos.filter(d=>d.tipo==='gabarito')){const o=capElemento('option',`${d.situacao_gabarito}: ${d.nome_original} · ${d.sha256.slice(0,10)}`);o.value=d.sha256;g.append(o);}
    const enviar=capElemento('button','Encaminhar prova + gabarito');enviar.type='button';enviar.disabled=!lote.liberado;enviar.onclick=async()=>{enviar.disabled=true;try{const d=await postarCaptacao('encaminhar',{lote:lote.id,gabarito_sha256:g.value});await atualizarCaptacao(lote.id);cap('aviso-captacao').textContent=`${d.protocolo}: pacote registrado na fila. Extração ainda não iniciada.`;}catch(e){cap('aviso-captacao').textContent='Erro: '+e.message;enviar.disabled=!lote.liberado;}};a.append(g,enviar);
    if(lote.encaminhamento){const f=document.createElement('form');f.append(capElemento('p','Registrar análise manual do usuário (não executa extração).'));const sel=document.createElement('select');sel.name='resultado';for(const v of ['concluida','falha']){const o=capElemento('option',v);o.value=v;sel.append(o);}sel.setAttribute('aria-label','Resultado da análise');const rel=document.createElement('textarea');rel.required=true;rel.name='relatorio';rel.placeholder='Descreva o resultado da análise realizada';rel.setAttribute('aria-label','Relatório da análise');const b=capElemento('button','Registrar análise manual');b.type='submit';f.append(sel,rel,b);f.onsubmit=e=>{e.preventDefault();executarCaptacao(f,async()=>{await postarCaptacao('registrar_analise',{lote:lote.id,encaminhamento:lote.encaminhamento,resultado:sel.value,relatorio:rel.value});await atualizarCaptacao(lote.id);cap('aviso-captacao').textContent='Análise declarada pelo usuário registrada no histórico.';});};a.append(f);}
    const detalhes=document.createElement('details');detalhes.append(capElemento('summary','Registro e histórico'),capElemento('pre',JSON.stringify(lote,null,2)));a.append(detalhes);cap('lista-lotes').append(a);
  }
}
function cancelarIdentificacao(){cap('identificar-legado').value='';cap('salvar-protocolo').textContent='Registrar prova';cap('cancelar-identificacao').hidden=true;}
cap('cancelar-identificacao').onclick=cancelarIdentificacao;cap('busca-protocolo').oninput=mostrarRegistro;cap('filtros-protocolo').onsubmit=e=>e.preventDefault();cap('filtros-protocolo').onreset=()=>setTimeout(mostrarRegistro,0);
let catalogosCaptacao={orgaos:{},cargos:{}};
fetch('/api/catalogos').then(r=>r.json()).then(d=>{catalogosCaptacao=d;for(const [id,nome]of Object.entries(d.orgaos||{})){const o=capElemento('option',nome);o.value=id;cap('cap-orgaos').append(o);}}).catch(()=>{});
cap('cap-orgao-id').onchange=()=>{const id=cap('cap-orgao-id').value;if(catalogosCaptacao.orgaos[id])cap('cap-orgao-nome').value=catalogosCaptacao.orgaos[id];cap('cap-cargos').replaceChildren();for(const [key,nome]of Object.entries(catalogosCaptacao.cargos)){if(key.startsWith(id+'.')){const o=capElemento('option',nome);o.value=key.split('.')[1];cap('cap-cargos').append(o);}}};
cap('cap-cargo-id').onchange=()=>{const nome=catalogosCaptacao.cargos[cap('cap-orgao-id').value+'.'+cap('cap-cargo-id').value];if(nome)cap('cap-cargo-nome').value=nome;};
