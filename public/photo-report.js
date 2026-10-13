import {evidenceRows,escapeEvidence as e} from './field-media.js';
const strings={en:{title:'Photographic work report 2.0',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',contents:'Contents',tasks:'Recorded tasks',field:'Field records',noPhotos:'No photos recorded for this unit.',none:'No photos match the selected filters.',unassigned:'Unit not assigned',general:'Units',coax:'Coaxial cabling',condensers:'Condensers',photo:'Photo',source:'Source',task:'Task',note:'Field record',before:'Initial conditions',during:'During work',after:'After completion',unspecified:'Stage not specified',status:'Recorded status',complete:'Completed',todo:'Pending',date:'Recorded date',historical:'Photo dates and field notes document their recorded conditions. A completed task does not by itself confirm inspection or testing.',filters:'Applied filters',all:'Whole project',language:'Report language',print:'Print / PDF',close:'Close',original:'Names and field descriptions are preserved in their original language.',missing:'Images failed to load. Retry loading images before printing.',retry:'Retry images',wait:'Loading full-size photos…',without:'Tasks without photos',unfiltered:'Field records are included only when their category or linked tasks match task filters.',context:'Unit context',part:'Part',of:'of'},pt:{title:'Relatório fotográfico da obra 2.0',units:'Unidades / grupos de trabalho',photos:'Fotos únicas',done:'Tarefas concluídas',pending:'Tarefas pendentes',contents:'Índice',tasks:'Tarefas registradas',field:'Registros de campo',noPhotos:'Nenhuma foto registrada nesta unidade.',none:'Nenhuma foto corresponde aos filtros selecionados.',unassigned:'Unidade não definida',general:'Unidades',coax:'Cabeamento coaxial',condensers:'Condensers',photo:'Foto',source:'Origem',task:'Tarefa',note:'Registro de campo',before:'Condições iniciais',during:'Durante o trabalho',after:'Após a conclusão',unspecified:'Etapa não informada',status:'Situação registrada',complete:'Concluída',todo:'Pendente',date:'Data registrada',historical:'As datas e notas documentam as condições na época do registro. Uma tarefa concluída não confirma, por si só, inspeção ou testes.',filters:'Filtros aplicados',all:'Obra completa',language:'Idioma do relatório',print:'Imprimir / PDF',close:'Fechar',original:'Nomes e descrições de campo são preservados no idioma original.',missing:'Algumas imagens não carregaram. Tente carregar novamente antes de imprimir.',retry:'Recarregar imagens',wait:'Carregando fotos em tamanho completo…',without:'Tarefas sem fotos',unfiltered:'Com filtros de tarefas, os registros de campo só entram quando a categoria ou as tarefas vinculadas correspondem.',context:'Contexto da unidade',part:'Parte',of:'de'}};
const validURL=url=>typeof url==='string'&&/^(https?:\/\/|data:image\/|blob:)/i.test(url);
const identity=url=>{try{const u=new URL(url);if(u.hostname==='firebasestorage.googleapis.com')return u.origin+u.pathname;}catch{}return url;};
const dateValue=v=>{if(v?.seconds)return v.seconds*1000;if(v?.toDate)return +v.toDate();if(typeof v==='string'){const d=Date.parse(v);return Number.isFinite(d)?d:0;}return 0;};
const dateLabel=(v,lang)=>{const t=dateValue(v);return t?new Date(t).toLocaleDateString(lang==='pt'?'pt-BR':'en-US',{timeZone:'America/New_York',year:'numeric',month:'short',day:'numeric'}):typeof v==='string'?v:'';};
const stageKey=p=>({'before-installation':'before','during-work':'during','after-work':'after','after-completion':'after'}[p]||'unspecified');
export function buildPhotoModel({project,rooms,tasks,notes,filters={},floorOrder=[]}){
 const restrictive=Boolean(filters.task||filters.tech||filters.status&&filters.status!=='all'||filters.system&&filters.system!=='all');
 const selected=rooms.filter(r=>(!filters.floor||filters.floor==='all'||(r.floor||'Other')===filters.floor)&&(!filters.units?.length||filters.units.includes(r.id)));
 const allowed=new Set(selected.map(r=>r.id));
 const roomIds=new Set(rooms.map(r=>r.id));
 const scopedTasks=tasks.filter(t=>allowed.has(t.roomId)||(!roomIds.has(t.roomId)&&(!filters.floor||filters.floor==='all')&&!filters.units?.length));
 const taskIds=new Set(scopedTasks.map(t=>t.id));
 const scopedNotes=notes.filter(n=>(allowed.has(n.roomId)||!roomIds.has(n.roomId)&&(!filters.floor||filters.floor==='all')&&!filters.units?.length)&&(!restrictive||n.linkedTaskIds?.some(id=>taskIds.has(id))||(!filters.task&&!filters.tech&&(!filters.status||filters.status==='all')&&n.cat===filters.system)));
 const hasUnassigned=scopedTasks.some(t=>!roomIds.has(t.roomId))||scopedNotes.some(n=>!roomIds.has(n.roomId));
 if(hasUnassigned)selected.push({id:'__unassigned',name:'',unassigned:true});
 selected.sort((a,b)=>{const ca=/^(roof|condensers)$/i.test(a.name?.trim())?1:0,cb=/^(roof|condensers)$/i.test(b.name?.trim())?1:0;if(ca!==cb)return ca-cb;const ai=floorOrder.indexOf(a.floor),bi=floorOrder.indexOf(b.floor);return (ai<0?999:ai)-(bi<0?999:bi)||String(a.name).localeCompare(String(b.name),undefined,{numeric:true});});
 const globalPhotos=new Map();let number=0;
 const units=selected.map(room=>{
  const matches=r=>room.unassigned?!roomIds.has(r.roomId):r.roomId===room.id;
  const rt=scopedTasks.filter(matches),rn=scopedNotes.filter(matches).sort((a,b)=>dateValue(a.createdAt||a.savedAt)-dateValue(b.createdAt||b.savedAt));
  const photos=new Map();
  const add=(record,source,description,date,phase)=>{
   for(const row of evidenceRows(record).filter(p=>p.type==='image'&&validURL(p.url))){
    const key=identity(row.url),reference={source,description,date,stage:stageKey(phase),name:row.name||'',status:source==='task'?(record.done?'complete':'todo'):null};
    if(photos.has(key)){photos.get(key).references.push(reference);continue;}
    const photo={url:row.url,references:[reference],number:++number,shared:globalPhotos.get(key)?.number||null};
    if(!globalPhotos.has(key))globalPhotos.set(key,photo);
    photos.set(key,photo);
   }
  };
  // Context is included only for a whole-unit view, never through a restrictive task filter.
  if(!restrictive){add({photoUrl:room.photos?.before,photos:room.scopeBrief?.photos||[],attachments:room.scopeBrief?.attachments||[]},'context',room.scopeBrief?.before||room.scopeBrief?.workScope||'',null,'before-installation');add({photoUrl:room.photos?.after},'context','',null,'after-work');}
  rt.forEach(t=>add(t,'task',t.name+(t.reportBrief?' — '+t.reportBrief:''),t.doneAt||t.updatedAt||t.createdAt,t.phase));
  rn.forEach(n=>add(n,'note',[n.text,n.difficulties,n.impact,n.nextStep].filter(Boolean).join('\n'),n.createdAt||n.savedAt,n.phase));
  const condenser=/^(roof|condensers)$/i.test(room.name?.trim());
  return {room,tasks:rt,notes:rn,photos:[...photos.values()],service:condenser?'condensers':/coax/i.test(project.name||'')?'coax':'general'};
 }).filter(u=>u.tasks.length||u.notes.length||u.photos.length);
 return {project,units,filters,restrictive,totalPhotos:globalPhotos.size,done:scopedTasks.filter(t=>t.done).length,pending:scopedTasks.filter(t=>!t.done).length};
}
export const photoReportCSS=`
.pr-report{max-width:850px;margin:auto;background:#fff;color:#17212b;font:13px/1.45 Arial,sans-serif;overflow-wrap:anywhere}.pr-report *{box-sizing:border-box}.pr-report h1{font-size:28px;margin:0 0 8px}.pr-report h2{font-size:22px;margin:0 0 8px}.pr-report h3{font-size:17px;margin:0 0 8px}.pr-cover{padding:22px 0}.pr-brand{font-size:12px;letter-spacing:2px;color:#6b541e;font-weight:bold;margin-bottom:14px}.pr-muted{color:#52616f;font-size:11px}.pr-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:20px 0}.pr-kpis div{padding:12px;border:1px solid #d9dfe5}.pr-kpis strong{display:block;font-size:25px}.pr-index{width:100%;border-collapse:collapse}.pr-index td,.pr-index th{padding:7px;text-align:left;border-bottom:1px solid #d9dfe5}.pr-index a{color:inherit;text-decoration:none}.pr-unit{margin-top:28px}.pr-unit-head{border-top:4px solid #b48a32;padding-top:14px;break-after:avoid}.pr-tasks{padding-left:20px}.pr-tasks li{padding:2px 0}.pr-sheet{margin:20px 0;padding-top:12px;border-top:1px solid #d9dfe5}.pr-sheet-head{margin-bottom:10px;break-after:avoid}.pr-gallery{display:grid;grid-template-columns:1fr;gap:14px}.pr-photo{margin:0;break-inside:avoid;page-break-inside:avoid}.pr-photo img{display:block;width:100%;height:300px;object-fit:contain;background:#f6f7f8;border:1px solid #d9dfe5}.pr-photo figcaption{padding:8px 0;white-space:pre-wrap;font-size:11px}.pr-photo a{color:#243e54}.pr-reference{margin:4px 0}.pr-warning{border:1px solid #b45309;background:#fff8e6;padding:10px;white-space:pre-wrap}.pr-report-bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:12px;background:#f0f2f4;color:#17212b;margin-bottom:15px}.pr-report-bar select,.pr-report-bar button{min-height:40px;padding:6px 12px;color:#17212b;background:white;border:1px solid #aab4bd;border-radius:5px}.pr-load-status:empty{display:none}@media(max-width:500px){.pr-kpis{grid-template-columns:1fr 1fr}.pr-photo img{height:260px}}@media print{@page{size:Letter;margin:12mm}.pr-report{max-width:none;font-size:11px}.pr-report-bar,.pr-load-status{display:none!important}.pr-unit,.pr-sheet{break-before:page;page-break-before:always}.pr-unit{margin:0}.pr-sheet{margin:0;border:0;padding:0}.pr-photo img{height:66mm}.pr-gallery{gap:5mm}.pr-photo figcaption{font-size:10px;line-height:1.35}.pr-cover{padding:0}.pr-index tr,.pr-kpis{break-inside:avoid}.pr-report a{text-decoration:none;color:inherit}}
`;
export function renderPhotoReport(model,language='en'){
 const l=strings[language]||strings.en,roomName=u=>u.room.unassigned?l.unassigned:u.service==='condensers'?l.condensers:u.room.name;
 const filterText=Object.entries(model.filters).filter(([k,v])=>['floor','system','status','task','tech','units'].includes(k)&&v&&v!=='all'&&(!Array.isArray(v)||v.length)).map(([k,v])=>k+': '+(Array.isArray(v)?model.units.map(roomName).join(', '):v)).join(' · ')||l.all;
 let html='<article class="pr-report"><header class="pr-cover"><div class="pr-brand">OBRA MANAGER · FIELD DOCUMENTATION</div><h1>'+e(model.project.name)+'</h1><h2>'+l.title+'</h2><p>'+e(model.project.address||'')+'</p><p class="pr-muted">'+dateLabel(new Date().toISOString(),language)+'</p><p class="pr-muted">'+l.filters+': '+e(filterText)+'</p><div class="pr-kpis">'+[[model.units.length,l.units],[model.totalPhotos,l.photos],[model.done,l.done],[model.pending,l.pending]].map(([n,t])=>'<div><strong>'+n+'</strong>'+t+'</div>').join('')+'</div><p class="pr-muted">'+l.historical+'</p><p class="pr-muted">'+l.original+'</p>'+(model.restrictive?'<p class="pr-muted">'+l.unfiltered+'</p>':'')+'<h3>'+l.contents+'</h3><table class="pr-index"><thead><tr><th>'+l.units+'</th><th>'+l.photos+'</th><th>'+l.pending+'</th></tr></thead><tbody>'+model.units.map((u,i)=>'<tr><td><a href="#pr-unit-'+i+'">'+e(l[u.service]+' · '+roomName(u))+'</a></td><td>'+u.photos.length+'</td><td>'+u.tasks.filter(t=>!t.done).length+'</td></tr>').join('')+'</tbody></table></header>';
 if(!model.units.length)html+='<p>'+l.none+'</p>';
 model.units.forEach((u,i)=>{
  const label=l[u.service]+' · '+roomName(u);
  html+='<section class="pr-unit" id="pr-unit-'+i+'"><header class="pr-unit-head"><p class="pr-muted">'+e(l[u.service])+'</p><h2>'+e(roomName(u))+'</h2><p>'+e(u.room.floor||'')+' · '+u.photos.length+' '+l.photos+'</p></header><h3>'+l.tasks+'</h3><ul class="pr-tasks">'+u.tasks.map(t=>'<li><strong>'+e(t.name)+'</strong> · '+l[t.done?'complete':'todo']+(t.doneAt?' · '+e(dateLabel(t.doneAt,language)):'')+(evidenceRows(t).some(p=>p.type==='image')?'':' · '+l.without)+'</li>').join('')+'</ul>'+(u.photos.length?'':'<p>'+l.noPhotos+'</p>');
  for(let j=0;j<u.photos.length;j+=2){
   html+='<section class="pr-sheet"><header class="pr-sheet-head"><h3>'+e(label)+'</h3><div class="pr-muted">'+l.part+' '+(j/2+1)+' '+l.of+' '+Math.ceil(u.photos.length/2)+'</div></header><div class="pr-gallery">';
   u.photos.slice(j,j+2).forEach(p=>{
    html+='<figure class="pr-photo"><a href="'+e(p.url)+'" target="_blank" rel="noopener"><img loading="eager" src="'+e(p.url)+'" alt="'+e(label+' · '+l.photo+' '+p.number)+'"></a><figcaption><strong>'+l.photo+' '+p.number+' · '+e(roomName(u))+'</strong>'+p.references.map(ref=>'<div class="pr-reference"><b>'+l[ref.source]+(ref.status?' · '+l[ref.status]:'')+'</b>'+(ref.date?' · '+e(dateLabel(ref.date,language)):'')+' · '+l[ref.stage]+(ref.description?'\n'+e(ref.description):'')+(ref.name?'\n'+e(ref.name):'')+'</div>').join('')+'</figcaption></figure>';
   });
   html+='</div></section>';
  }
  html+='</section>';
 });
 return html+'</article>';
}
export function installPhotoReport(){
 let input,language='en';
 const draw=()=>{const model=buildPhotoModel(input),l=strings[language];const el=document.getElementById('pdf-content');el.lang=language==='pt'?'pt-BR':'en';el.innerHTML='<style>'+photoReportCSS+'</style><div class="pr-report-bar"><label>'+l.language+' <select id="pr-language"><option value="en">English</option><option value="pt">Português</option></select></label><button id="pr-retry">'+l.retry+'</button></div><div class="pr-load-status" role="status"></div>'+renderPhotoReport(model,language);const select=el.querySelector('#pr-language');select.value=language;select.onchange=()=>{language=select.value;draw();};el.querySelector('#pr-retry').onclick=()=>{el.querySelectorAll('img').forEach(img=>{if(!img.complete||!img.naturalWidth){const src=img.getAttribute('src');img.removeAttribute('src');img.src=src;}});};};
 async function print(el){
  // Open synchronously so mobile browsers keep the user gesture permission.
  const w=window.open('','_blank','width=950,height=800');if(!w)return;
  const l=strings[language];w.document.write('<!doctype html><html lang="'+(el.lang||'en')+'"><head><meta charset="utf-8"><title>'+e(input.project.name+' — '+l.title)+'</title><style>'+photoReportCSS+'</style></head><body><div class="pr-report-bar"><span id="pr-print-status">'+l.wait+'</span><button id="pr-print-retry" hidden>'+l.retry+'</button></div>'+el.querySelector('.pr-report').outerHTML+'</body></html>');w.document.close();
  const load=async()=>{const retry=w.document.getElementById('pr-print-retry'),status=w.document.getElementById('pr-print-status');retry.hidden=true;status.textContent=l.wait;const imgs=[...w.document.images];const settled=await Promise.all(imgs.map(img=>new Promise(resolve=>{if(img.complete)return resolve(img.naturalWidth>0);const finish=ok=>{clearTimeout(timer);img.onload=null;img.onerror=null;resolve(ok);};const timer=setTimeout(()=>finish(false),30000);img.onload=()=>finish(img.naturalWidth>0);img.onerror=()=>finish(false);})));
   if(w.closed)return;if(settled.some(ok=>!ok)){status.textContent=l.missing;retry.hidden=false;retry.onclick=()=>{imgs.forEach(img=>{if(!img.complete||!img.naturalWidth){const src=img.getAttribute('src');img.removeAttribute('src');img.src=src;}});load();};return;}
   status.textContent='';w.focus();w.print();
  };await load();
 }
 window.photoReport={open:data=>{input=data;draw();document.getElementById('pdf-report').classList.add('open');},print};
}
