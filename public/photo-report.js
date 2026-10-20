import {photoRole,orderPhotos,reportSheets} from './report-photo-order.js?v=1';
import {coverLabels,facadePhotoURL,coverPhotoLabels} from './photo-report-cover.js?v=2';
import {exportPhotoReportPDF} from './photo-report-pdf.js?v=roomfix20261020';
import {progressPercent} from './work-progress.js?v=1';
import {evidenceRows,escapeEvidence as e} from './field-media.js';
const strings={en:{title:'Photographic work report 2.0',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',contents:'Contents',tasks:'Recorded tasks',field:'Field records',noPhotos:'No photos recorded for this unit.',none:'No photos match the selected filters.',unassigned:'Unit not assigned',general:'Units',coax:'Coaxial cabling',condensers:'Condensers',photo:'Photo',source:'Source',task:'Task',note:'Field record',before:'Initial conditions',during:'During work',after:'After completion',unspecified:'Stage not specified',status:'Recorded status',complete:'Completed',todo:'Pending',date:'Recorded date',historical:'Photo dates and field notes document their recorded conditions. A completed task does not by itself confirm inspection or testing.',filters:'Applied filters',all:'Whole project',language:'Report language',print:'Print / PDF',close:'Close',original:'Names and field descriptions are preserved in their original language.',missing:'Images failed to load. Retry loading images before printing.',retry:'Retry images',wait:'Loading full-size photos…',without:'Tasks without photos',unfiltered:'Field records are included only when their category or linked tasks match task filters.',context:'Unit context',part:'Part',of:'of'},pt:{title:'Relatório fotográfico da obra 2.0',units:'Unidades / grupos de trabalho',photos:'Fotos únicas',done:'Tarefas concluídas',pending:'Tarefas pendentes',contents:'Índice',tasks:'Tarefas registradas',field:'Registros de campo',noPhotos:'Nenhuma foto registrada nesta unidade.',none:'Nenhuma foto corresponde aos filtros selecionados.',unassigned:'Unidade não definida',general:'Unidades',coax:'Cabeamento coaxial',condensers:'Condensers',photo:'Foto',source:'Origem',task:'Tarefa',note:'Registro de campo',before:'Condições iniciais',during:'Durante o trabalho',after:'Após a conclusão',unspecified:'Etapa não informada',status:'Situação registrada',complete:'Concluída',todo:'Pendente',date:'Data registrada',historical:'As datas e notas documentam as condições na época do registro. Uma tarefa concluída não confirma, por si só, inspeção ou testes.',filters:'Filtros aplicados',all:'Obra completa',language:'Idioma do relatório',print:'Imprimir / PDF',close:'Fechar',original:'Nomes e descrições de campo são preservados no idioma original.',missing:'Algumas imagens não carregaram. Tente carregar novamente antes de imprimir.',retry:'Recarregar imagens',wait:'Carregando fotos em tamanho completo…',without:'Tarefas sem fotos',unfiltered:'Com filtros de tarefas, os registros de campo só entram quando a categoria ou as tarefas vinculadas correspondem.',context:'Contexto da unidade',part:'Parte',of:'de'}};
Object.assign(strings.en,{format:'Format',summary:'Summary',full:'Complete',details:'Include detailed records and field history',history:'Historical field records',historyNote:'Recorded conditions and plans at the date shown. These notes are historical; the current task register above reflects the latest recorded completion status.',current:'Current task register',record:'Record',photoList:'Related photos',taskNotes:'Recorded task notes'});
Object.assign(strings.pt,{format:'Formato',summary:'Resumido',full:'Completo',details:'Incluir registros detalhados e histórico de campo',history:'Histórico de campo',historyNote:'Condições e planos na data indicada. Estas notas são históricas; o quadro atual de tarefas acima mostra a situação de conclusão registrada mais recente.',current:'Situação atual das tarefas',record:'Registro',photoList:'Fotos relacionadas',taskNotes:'Notas registradas nas tarefas'});
Object.assign(strings.en,{progress:'Work progress',progressBasis:'Progress is based on the tasks included in this report. Completed subtasks contribute proportionally; completed-task counts remain separate.',noTasks:'No tasks recorded'});
Object.assign(strings.pt,{progress:'Progresso do serviço',progressBasis:'O progresso considera as tarefas incluídas neste relatório. As subtarefas concluídas contribuem proporcionalmente; a contagem de tarefas concluídas permanece separada.',noTasks:'Nenhuma tarefa registrada'});
const validURL=url=>typeof url==='string'&&/^(https?:\/\/|data:image\/|blob:)/i.test(url);
const identity=url=>{try{const u=new URL(url);if(u.hostname==='firebasestorage.googleapis.com'){const path=decodeURIComponent(u.pathname),name=path.split('/').pop().replace(/^\d+_/, '');return /^IMG_[A-Za-z0-9_()\-]+\.(?:jpe?g|png|heic)$/i.test(name)?'uploaded-photo:'+name:u.origin+u.pathname;}}catch{}return url;};
const administrative=t=>t.reportExcluded===true||/^(?:Punch-list reference|Record reference)\s*[—-]/i.test(t.name||'');
const dateValue=v=>{if(v?.seconds)return v.seconds*1000;if(v?.toDate)return +v.toDate();if(typeof v==='string'){const us=v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/),iso=v.match(/^(\d{4})-(\d{2})-(\d{2})$/);if(us)return Date.UTC(+us[3],+us[1]-1,+us[2],16);if(iso)return Date.UTC(+iso[1],+iso[2]-1,+iso[3],16);const d=Date.parse(v);return Number.isFinite(d)?d:0;}return 0;};
const dateLabel=(v,lang)=>{const t=dateValue(v);return t?new Date(t).toLocaleDateString(lang==='pt'?'pt-BR':'en-US',{timeZone:'America/New_York',year:'numeric',month:'short',day:'numeric'}):typeof v==='string'?v:'';};
const stageKey=p=>({'before-installation':'before','during-work':'during','after-work':'after','after-completion':'after'}[p]||'unspecified');
const storyStep=photo=>{
 const task=photo.references.find(r=>r.source==='task'),text=(task?.sourceTitle||task?.description||'').toLowerCase();
 if(photo.references.some(r=>r.stage==='before'))return {rank:0,key:'storyInitial'};
 if(/initial conditions|nameplate|review initial/.test(text))return {rank:0,key:'storyInitial'};
 if(/investigat|survey|staging|initial pull|collect materials/.test(text))return {rank:10,key:'storyPreparation'};
 if(/final check|test.*completed|test.*connection/.test(text)||photo.references.some(r=>r.stage==='after'))return {rank:50,key:'storyFinal'};
 if(/label|identify/.test(text))return {rank:40,key:'storyIdentification'};
 if(/measure|cut|secure and arrange/.test(text))return {rank:30,key:'storyFinishing'};
 if(/drill|entry access|pull|rout|install|connect|mount|penetration|support/.test(text)||photo.references.some(r=>r.stage==='during'))return {rank:20,key:'storyWork'};
 return {rank:25,key:'storyRecorded'};
};
Object.assign(strings.en,{storyInitial:'Initial conditions',storyPreparation:'Investigation and preparation',storyWork:'Work performed',storyFinishing:'Finishing and organization',storyIdentification:'Identification and labels',storyFinal:'Final checks and documented results',storyRecorded:'Supporting documentation'});
Object.assign(strings.pt,{storyInitial:'Condições iniciais',storyPreparation:'Investigação e preparação',storyWork:'Execução do serviço',storyFinishing:'Acabamento e organização',storyIdentification:'Identificação e etiquetas',storyFinal:'Verificações finais e resultados documentados',storyRecorded:'Documentação complementar'});
export function buildPhotoModel({project,rooms,tasks,notes,filters={},floorOrder=[]}){
 const restrictive=Boolean(filters.task||filters.tech||filters.status&&filters.status!=='all'||filters.system&&filters.system!=='all');
 const selected=rooms.filter(r=>(!filters.floor||filters.floor==='all'||(r.floor||'Other')===filters.floor)&&(!filters.units?.length||filters.units.includes(r.id)));
 const allowed=new Set(selected.map(r=>r.id));
 const roomIds=new Set(rooms.map(r=>r.id));
 const scopedTasks=tasks.filter(t=>!administrative(t)&&(allowed.has(t.roomId)||(!roomIds.has(t.roomId)&&(!filters.floor||filters.floor==='all')&&!filters.units?.length)));
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
    const key=identity(row.url),reference={source,description,reportRole:record.reportRole||row.reportRole||'',sourceTitle:source==='task'?record.name:'',sourceId:record.id||'',date,stage:stageKey(phase),name:row.name||'',status:source==='task'?(record.done?'complete':'todo'):null};
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
  return {room,tasks:rt,notes:rn,photos:[...photos.values()],service:condenser?'condensers':(/coax/i.test(project.name||'')||rt.some(t=>/coax/i.test(t.name||'')))?'coax':'general'};
 }).filter(u=>u.tasks.length||u.notes.length||u.photos.length);
 // A shared image is printed once; preserve all evidence references on that image.
 const unique=new Map();for(const u of units)u.photos=u.photos.filter(p=>{const key=identity(p.url);if(unique.has(key)){unique.get(key).references.push(...p.references);return false;}unique.set(key,p);return true;});
 let sequence=0;for(const unit of units){unit.photos=orderPhotos(unit.photos,p=>storyStep(p).rank);for(const photo of unit.photos)photo.number=++sequence;}
 return {project,units,filters,restrictive,totalPhotos:globalPhotos.size,done:scopedTasks.filter(t=>t.done).length,pending:scopedTasks.filter(t=>!t.done).length};
}
export const photoReportCSS=`
.pr-report{max-width:850px;margin:auto;padding:20px;background:#fff;color:#17212b;font:13px/1.45 Arial,sans-serif;overflow-wrap:anywhere}
.pr-report *{box-sizing:border-box}.pr-report h1{font-size:28px;margin:0 0 8px}.pr-report h2{font-size:22px;margin:0 0 8px}.pr-report h3{font-size:17px;margin:0 0 8px}
.pr-cover{padding:0 0 20px;break-after:page;page-break-after:always}.pr-cover-heading{background:#17212b;color:#fff;padding:24px;border-left:4px solid #b48a32}.pr-cover-heading .pr-brand{color:#d9ba6e;margin-bottom:14px;font-size:10px}.pr-cover-heading h1{font-size:30px;line-height:1.2;margin:12px 0}.pr-cover-heading h2{font-size:13px;font-weight:400;color:#d1dce5}.pr-cover-address{font-size:12px;color:#d1dce5;margin:10px 0 0}.pr-cover-photo{margin:18px 0 0;break-inside:avoid}.pr-cover-photo img{display:block;width:100%;height:340px;object-fit:contain;background:#f6f7f8;border:1px solid #d9dfe5}.pr-cover-photo figcaption{font-size:10px;color:#52616f;padding:7px 0}.pr-cover-placeholder{padding:30px;background:#f6f7f8;margin-top:18px;color:#52616f}.pr-overview{padding-top:10px}.pr-cover .pr-kpis{margin:18px 0}.pr-cover .pr-kpis div{background:#f6f7f8;border:0}.pr-brand{font-size:12px;letter-spacing:2px;color:#6b541e;font-weight:bold;margin-bottom:14px}.pr-muted{color:#52616f;font-size:11px}
.pr-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:20px 0}.pr-kpis div{padding:12px;border:1px solid #d9dfe5}.pr-kpis strong{display:block;font-size:25px}
.pr-index{width:100%;border-collapse:collapse}.pr-index td,.pr-index th{padding:7px;text-align:left;border-bottom:1px solid #d9dfe5}.pr-index th{overflow-wrap:normal}.pr-index a{color:inherit;text-decoration:none}.pr-progress-label strong{white-space:nowrap;flex-shrink:0}.pr-progress-compact .pr-progress-label{justify-content:flex-end}.pr-progress-compact .pr-progress-label span{display:none}
.pr-progress{margin:12px 0 16px;break-inside:avoid;min-width:0}.pr-progress-label{display:flex;justify-content:space-between;gap:12px;font-size:11px;color:#52616f;margin-bottom:5px}.pr-progress-label strong{font-size:14px;color:#17212b;font-variant-numeric:tabular-nums}.pr-progress-track{height:7px;background:#e6ecf0;border-radius:4px;overflow:hidden}.pr-progress-fill{height:100%;background:#b48a32;border-radius:4px;transform-origin:left;animation:pr-progress-enter .65s ease-out both}.pr-progress-complete{background:#39734c}.pr-progress-compact{margin:3px 0;min-width:90px}.pr-progress-compact .pr-progress-label{font-size:9px;gap:8px}.pr-progress-compact .pr-progress-label strong{font-size:12px}.pr-progress-compact .pr-progress-track{height:5px}
@keyframes pr-progress-enter{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@media(prefers-reduced-motion:reduce){.pr-progress-fill{animation:none}}
.pr-unit{margin-top:28px}.pr-unit-head{border-top:4px solid #b48a32;padding-top:12px;break-after:avoid}.pr-current{padding:8px 10px;background:#f1f5f7;margin:8px 0 14px;break-inside:avoid}
.pr-sheet{margin:20px 0;padding-top:10px;border-top:1px solid #d9dfe5}.pr-sheet-head{margin-bottom:8px;break-after:avoid}.pr-sheet-head h3{font-size:15px;margin:0}.pr-sheet-progress{display:none}
.pr-gallery{display:grid;grid-template-columns:1fr;gap:14px}.pr-photo{margin:0;break-inside:avoid;page-break-inside:avoid}.pr-photo img{display:block;width:100%;height:300px;object-fit:contain;background:#f6f7f8;border:1px solid #d9dfe5}
.pr-photo figcaption{padding:7px 0;font-size:11px;line-height:1.4}.pr-photo a{color:#243e54}.pr-reference{margin:3px 0}.pr-full img{height:480px}
.pr-summary .pr-gallery{grid-template-columns:1fr 1fr}.pr-summary .pr-photo img{height:240px}
.pr-history{margin-top:24px;border-top:4px solid #b48a32;padding-top:12px}.pr-record{margin:16px 0}.pr-record h3{break-after:avoid}.pr-record p{white-space:pre-wrap}.pr-warning{border:1px solid #b45309;background:#fff8e6;padding:10px}
.pr-report-bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:12px;background:#f0f2f4;color:#17212b;margin-bottom:15px}.pr-report-bar label{display:flex;gap:6px;align-items:center}
.pr-report-bar select,.pr-report-bar button{min-height:40px;padding:6px 12px;color:#17212b;background:white;border:1px solid #aab4bd;border-radius:5px}.pr-load-status:empty{display:none}
@media(max-width:500px){.pr-cover-heading{padding:18px}.pr-cover-heading h1{font-size:24px}.pr-cover-photo img{height:250px}.pr-report{padding:12px}.pr-kpis{grid-template-columns:1fr 1fr}.pr-photo img{height:260px}.pr-full img{height:400px}.pr-summary .pr-gallery{grid-template-columns:1fr}}
@media print{
 .pr-progress-fill{animation:none!important;transform:none!important}.pr-progress-track,.pr-progress-fill{print-color-adjust:exact;-webkit-print-color-adjust:exact}.pr-progress{margin:6px 0 10px}
 @page{size:Letter;margin:12mm 12mm 16mm;@bottom-right{content:counter(page) " / " counter(pages);font:9px Arial;color:#52616f}}
 html,body{margin:0!important;padding:0!important;width:auto!important;min-width:0!important;background:#fff!important}.pr-report{width:100%;max-width:none;padding:0;font-size:11px}.pr-report-bar,.pr-load-status{display:none!important}
 .pr-unit,.pr-history{break-before:page;page-break-before:always}.pr-unit{margin:0}.pr-unit:has(.pr-sheet){break-before:auto;page-break-before:auto}.pr-unit:has(.pr-sheet)>.pr-unit-head,.pr-unit:has(.pr-sheet)>.pr-current{display:none}.pr-sheet{margin:0;border:0;padding:0;break-before:page;page-break-before:always}.pr-sheet-head{break-inside:avoid;page-break-inside:avoid}.pr-sheet-progress{display:block}
 .pr-unit-head{padding-top:5px}.pr-unit-head p{margin:3px 0}.pr-unit-head h2{font-size:18px;margin:3px 0}.pr-current{padding:4px 6px;margin:4px 0 6px}.pr-sheet-head{margin-bottom:5px}
 .pr-summary .pr-gallery{grid-template-columns:1fr 1fr}.pr-summary .pr-photo img{height:80mm}.pr-summary .pr-full{grid-column:1/-1}.pr-summary .pr-full img{height:150mm}
 .pr-photo img{height:68mm;max-width:100%;object-fit:contain;object-position:center}.pr-gallery,.pr-summary .pr-gallery{display:block;font-size:0}.pr-photo{display:inline-block;vertical-align:top;width:100%;margin:0 0 4mm;font-size:10px;break-inside:avoid;page-break-inside:avoid}.pr-summary .pr-photo{width:calc(50% - 2mm);margin:0 1mm 4mm}.pr-summary .pr-full{width:100%;margin:0 0 4mm}.pr-photo figcaption{font-size:10px;line-height:1.3}.pr-full img{height:170mm}.pr-cover{padding:0;break-after:page;page-break-after:always}.pr-cover-heading{padding:7mm}.pr-cover-heading h1{font-size:25px}.pr-cover-photo img{height:85mm}.pr-overview{break-before:page;page-break-before:always}.pr-index tr,.pr-kpis{break-inside:avoid}.pr-report a{text-decoration:none;color:inherit}.pr-record p{orphans:3;widows:3}
}
`;
export const captionTitle=p=>{
 const task=p.references.find(r=>r.source==='task');
 if(task)return task.sourceTitle||task.description;
 const ref=p.references.find(r=>r.source==='context')||p.references[0];
 const text=(ref?.description||'').split(/\n|(?<=\.)\s/)[0].trim();
 return text.length>150?text.slice(0,147).replace(/\s+\S*$/,'')+'…':text;
};
export const photoSheets=(photos,summary=false)=>reportSheets(photos.map(p=>({...p,chapter:photoRole(p)==='facade'?'storyInitial':photoRole(p)==='map'?'context':storyStep(p).key})),summary);
function progressHTML(unit,l,compact=false){
 if(!unit.tasks.length)return '<div class="pr-muted">'+e(l.noTasks)+'</div>';
 const pct=progressPercent(unit.tasks),label=(unit.room.name||l.unassigned)+' - '+l.progress;
 return '<div class="pr-progress'+(compact?' pr-progress-compact':'')+'"><div class="pr-progress-label"><span>'+e(l.progress)+'</span><strong>'+pct+'%</strong></div><div class="pr-progress-track" role="progressbar" aria-label="'+e(label)+'" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+pct+'"><div class="pr-progress-fill'+(pct===100?' pr-progress-complete':'')+'" style="width:'+pct+'%"></div></div></div>';
}
export function renderPhotoReport(model,language='en',includeHistory=false){
 const l=strings[language]||strings.en,roomName=u=>u.room.unassigned?l.unassigned:u.service==='condensers'?l.condensers:u.room.name;
 const unitLabel=u=>u.service==='general'?[u.room.floor,roomName(u)].filter(Boolean).join(' · '):u.service==='condensers'?roomName(u):l[u.service]+' · '+roomName(u);
 const filterText=Object.entries(model.filters).filter(([k,v])=>['floor','system','status','task','tech','units'].includes(k)&&v&&v!=='all'&&(!Array.isArray(v)||v.length)).map(([k,v])=>k+': '+(Array.isArray(v)?model.units.map(roomName).join(', '):v)).join(' · ')||l.all;
 const cover=coverPhotoLabels(model.project,language),facadeURL=facadePhotoURL(model.project);
 let html='<article class="pr-report'+(!includeHistory?' pr-summary':'')+'"><header class="pr-cover"><div class="pr-cover-heading"><div class="pr-brand">OBRA MANAGER / FIELD DOCUMENTATION</div><h2>'+l.title+'</h2><h1>'+e(model.project.name)+'</h1>'+(model.project.address&&model.project.address!==model.project.name?'<p class="pr-cover-address">'+e(model.project.address)+'</p>':'')+'</div>'
  +(facadeURL?'<figure class="pr-cover-photo"><img crossorigin="anonymous" loading="eager" src="'+e(facadeURL)+'" alt="'+e(cover.facade)+'"><figcaption>'+e(cover.facade)+' / '+e(cover.context)+'</figcaption></figure>':'')
  +'<div class="pr-kpis">'+[[model.units.length,l.units],[model.totalPhotos,l.photos],[model.done,l.done],[model.pending,l.pending]].map(([n,t])=>'<div><strong>'+n+'</strong>'+t+'</div>').join('')+'</div><p class="pr-muted">'+e(cover.issued)+': '+dateLabel(new Date().toISOString(),language)+'</p></header>'
  +'<section class="pr-overview"><h2>'+l.contents+'</h2><p class="pr-muted">'+l.filters+': '+e(filterText)+'</p><p class="pr-muted">'+l.historical+'</p><p class="pr-muted">'+l.progressBasis+'</p><table class="pr-index"><thead><tr><th>'+l.units+'</th><th>'+l.photos+'</th><th>'+l.pending+'</th><th>'+l.progress+'</th></tr></thead><tbody>'+model.units.map((u,i)=>'<tr><td><a href="#pr-unit-'+i+'">'+e(unitLabel(u))+'</a></td><td>'+u.photos.length+'</td><td>'+u.tasks.filter(t=>!t.done).length+'</td><td>'+progressHTML(u,l,true)+'</td></tr>').join('')+'</tbody></table></section>';

 if(!model.units.length)html+='<p>'+l.none+'</p>';
 model.units.forEach((u,i)=>{
  const pending=u.tasks.filter(t=>!t.done),completed=u.tasks.filter(t=>t.done).length;
  html+='<section class="pr-unit" id="pr-unit-'+i+'"><header class="pr-unit-head"><p class="pr-muted">'+e(l[u.service])+'</p><h2>'+e(roomName(u))+'</h2><p class="pr-muted">'+e(u.room.floor||'')+' · '+u.photos.length+' '+l.photos+'</p>'+progressHTML(u,l)+'</header><div class="pr-current"><b>'+l.current+':</b> '+completed+'/'+u.tasks.length+' '+l.complete+' · '+pending.length+' '+l.pending+(pending.length?'<ul>'+pending.map(t=>'<li>'+e(t.name)+'</li>').join('')+'</ul>':'')+'</div>';
  const sheets=photoSheets(u.photos,!includeHistory);
  sheets.forEach((sheet,j)=>{
   const chapters=new Set(sheet.map(p=>p.chapter)),heading=chapters.size===1?l[sheet[0].chapter]:l.photos;
   html+='<section class="pr-sheet"><header class="pr-sheet-head"><h3>'+e(unitLabel(u))+' · '+(j===0?l.context:heading)+'</h3><div class="pr-muted">'+l.part+' '+(j+1)+' '+l.of+' '+sheets.length+'</div><div class="pr-sheet-progress">'+progressHTML(u,l)+'</div></header><div class="pr-gallery">';
   sheet.forEach(p=>{
    const ref=p.references.find(r=>r.source==='task')||p.references[0],title=captionTitle(p),stage=p.references.find(r=>r.stage!=='unspecified')?.stage;
    const meta=[ref?.status?l[ref.status]:l.history,ref?.date?l.date+': '+dateLabel(ref.date,language):'',stage?l[stage]:''].filter(Boolean).join(' · ');
    html+='<figure class="pr-photo'+(p.fullPage?' pr-full':'')+'"><a href="'+e(p.url)+'" target="_blank" rel="noopener"><img loading="eager" src="'+e(p.url)+'" alt="'+e(unitLabel(u)+' · '+l.photo+' '+p.number)+'"></a><figcaption><strong>'+l.photo+' '+p.number+' · '+e(roomName(u))+'</strong>'+(title?'<div class="pr-reference">'+e(title)+'</div>':'')+'<div class="pr-muted">'+e(meta)+'</div></figcaption></figure>';
   });
   html+='</div></section>';
  });
  if(!u.photos.length)html+='<p>'+l.noPhotos+'</p>';
  html+='</section>';
 });
 if(includeHistory){
  html+='<section class="pr-history"><h2>'+l.history+'</h2><p class="pr-warning">'+l.historyNote+'</p>';
  model.units.forEach((u,i)=>{
   html+='<h2>'+e(unitLabel(u))+'</h2>';
   const taskNotes=u.tasks.filter(t=>t.reportBrief||t.note);
   if(taskNotes.length)html+='<h3>'+l.taskNotes+'</h3>'+taskNotes.map(t=>'<article class="pr-record"><b>'+e(t.name)+'</b><p>'+e(t.reportBrief||t.note)+'</p></article>').join('');
   u.notes.forEach((note,n)=>{
    const photos=u.photos.filter(p=>p.references.some(ref=>ref.source==='note'&&ref.sourceId===note.id));
    html+='<article class="pr-record" id="pr-record-'+i+'-'+n+'"><h3>'+l.record+' '+(n+1)+' · '+e(dateLabel(note.createdAt||note.savedAt,language))+'</h3><p>'+e([note.text,note.difficulties,note.impact,note.nextStep].filter(Boolean).join('\n'))+'</p>'+(photos.length?'<p class="pr-muted">'+l.photoList+': '+photos.map(p=>p.number).join(', ')+'</p>':'')+'</article>';
   });
  });
  html+='</section>';
 }
 return html+'</article>';
}
export function installPhotoReport(){
 let input,language='en',includeHistory=false;
 const draw=()=>{const model=buildPhotoModel(input),l=strings[language];const el=document.getElementById('pdf-content');el.lang=language==='pt'?'pt-BR':'en';el.innerHTML='<style>'+photoReportCSS+'</style><div class="pr-report-bar"><label>'+l.language+' <select id="pr-language"><option value="en">English</option><option value="pt">Português</option></select></label><label>'+l.format+' <select id="pr-format"><option value="summary">'+l.summary+'</option><option value="complete">'+l.full+'</option></select></label><button id="pr-retry">'+l.retry+'</button></div><div class="pr-load-status" role="status"></div>'+renderPhotoReport(model,language,includeHistory);const printButton=document.querySelector('#pdf-report .pdf-topbar .print');if(printButton)printButton.textContent=language==='pt'?'Salvar / compartilhar PDF':'Save / Share PDF';const format=el.querySelector('#pr-format');format.value=includeHistory?'complete':'summary';format.onchange=()=>{includeHistory=format.value==='complete';draw();};const select=el.querySelector('#pr-language');select.value=language;select.onchange=()=>{language=select.value;draw();};el.querySelector('#pr-retry').onclick=()=>{el.querySelectorAll('img').forEach(img=>{if(!img.complete||!img.naturalWidth){const src=img.getAttribute('src');img.removeAttribute('src');img.src=src;}});};};
 async function print(el){
  return exportPhotoReportPDF(buildPhotoModel(input),{language,includeHistory,strings:strings[language],captionTitle,photoSheets});
 }

 window.photoReport={open:data=>{input=data;includeHistory=data.filters?.photoFormat==='complete';draw();document.getElementById('pdf-report').classList.add('open');},print};
}
