'use strict';
// Dashboard público: no hay token, Gemini API Key ni llamadas externas desde el navegador.
const $ = (id) => document.getElementById(id);
const stateIcon = (state) => state === 'success' ? '✓' : state === 'failure' ? '×' : '•';
const stateClass = (state) => state === 'success' ? '' : state === 'failure' ? ' failure' : ' other';
const statusText = (s) => ({success:'Exitoso',failure:'Fallido',cancelled:'Cancelado',skipped:'Omitido',pending:'Pendiente'}[s] || 'En curso');
const dateText = (s) => {
  if (!s) return 'Sin fecha';
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? 'Fecha no disponible' : d.toLocaleString('es-MX',{dateStyle:'medium',timeStyle:'short',timeZone:'UTC'})+' UTC';
};
function setText(id,text){ const el=$(id); if (el) el.textContent = String(text ?? '—'); }
function link(id,url){if (typeof url==='string' && url.startsWith('https://github.com/')) $(id)?.setAttribute('href',url);}
function el(tag,cls,text){const n=document.createElement(tag); if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n;}
function safeRun(r){return r && typeof r.url==='string'&&r.url.startsWith('https://github.com/')}
function renderRow(item, type){
 const row=el('div',type==='ai'?'ai-row':type==='security'?'security-row':'run-row');
 const icon=el('div','row-state'+stateClass(item.conclusion),stateIcon(item.conclusion));
 const copy=el('div','row-description');copy.append(el('strong','',item.name||'Workflow de GitHub Actions'));
 const more=[statusText(item.conclusion),item.branch||'rama desconocida',dateText(item.created_at)].join(' · ');
 copy.append(el('small','',more));
 const a=el('a','row-link','↗'); a.href=item.url;a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('aria-label','Ver ejecución en GitHub');
 row.append(icon,copy,a);return row;
}
function rowsTo(target, runs, count, type){
 const node=$(target);if(!node)return;node.replaceChildren();
 const useful=runs.filter(safeRun).slice(0,count);
 if(!useful.length){node.append(el('div','empty','No hay ejecuciones disponibles dentro de la muestra consultada.'));return;}
 for(const item of useful)node.append(renderRow(item,type));
}
function setSync(status){
 const x=$('sync-indicator');
 x.className='sync-pill'+(status==='synced'?'':status==='partial'?' pending':' error');
 x.textContent=status==='synced'?'● Datos sincronizados':status==='partial'?'● Sincronización parcial':'● Sin datos actualizados';
}
function render(data){
 const runs=Array.isArray(data.runs)?data.runs:[];
 const stats=data.stats||{};
 const links=data.links||{};
 const img=data.image||{};
 const repo=data.repository||{};
 setSync(data.status);
 setText('last-sync','Actualizado: '+dateText(data.generated_at));
 const synchronized = data.status === 'synced' || data.status === 'partial';
 setText('metric-total',synchronized && Number.isFinite(stats.total)?stats.total:'—');
 setText('metric-success',synchronized && Number.isFinite(stats.success)?stats.success:'—');
 setText('metric-failed',synchronized && Number.isFinite(stats.failure)?stats.failure:'—');
 setText('metric-success-note',runs.length?Math.round((stats.success||0)/runs.length*100)+'% de la muestra consultada':'Sin datos actualizados');
 setText('metric-image',img.available?'Publicada':'Sin verificar');
 setText('image-badge',img.available?'Inspeccionada':'No verificada');
 $('image-badge').className='badge'+(img.available?'':' neutral');
 if(img.reference)setText('image-ref',img.reference);
 setText('image-arch',img.available?[img.os,img.architecture].filter(Boolean).join(' / '):'Pendiente de inspección');
 setText('image-digest',img.digest||'No disponible');
 setText('image-description',(img.labels||{})['org.opencontainers.image.description']||'Imagen OCI ejecutable de validación; la inferencia Gemini se realiza en GitHub Actions.');
 setText('sha-tag',img.tags&&img.tags.find(t=>t.startsWith('sha-'))||'SHA pendiente');
 rowsTo('run-list',runs.filter(r=>['ci','cd','other'].includes(r.category)),6,'run');
 rowsTo('ai-runs',runs.filter(r=>r.category==='ai'),4,'ai');
 rowsTo('security-runs',runs.filter(r=>r.category==='security'),4,'security');
 const bind={
   'nav-repo':repo.url,'head-github':repo.url,'nav-actions':links.actions,'hero-actions':links.actions,
   'nav-package':links.package,'hero-package':links.package,'package-link':links.package,
   'ci-link':links.ci,'ai-link':links.ai,'security-link':links.security,'inspect-link':links.inspector
 };
 for(const [id,url] of Object.entries(bind))link(id,url);
 const warnings=$('warnings');warnings.replaceChildren();
 for(const warning of (data.warnings||[]).slice(0,3))warnings.append(el('p','',`Aviso de datos: ${warning}`));
}
async function init(){
 try{
  const url=new URL('./data/dashboard.json',location.href);
  const response=await fetch(url,{cache:'no-store'});
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  const data=await response.json();
  if(data.schema_version!==1)throw new Error('Esquema desconocido');
  render(data);
 }catch(error){
  setSync('error');
  const text='Datos no disponibles. Ejecuta «Plataforma DevOps | Publicar dashboard GitHub Pages» desde Actions.';
  $('warnings').append(el('p','',text));
 }
}
window.addEventListener('DOMContentLoaded',init);
