// One report contract for every unit. No remote summarization and no record mutations.
import {translateText,translations} from './unit-report-language.js?v=5';
const clean=v=>String(v??'').trim();
const safeURL=v=>{try{const u=new URL(String(v),'https://example.invalid');return ['http:','https:'].includes(u.protocol)?String(v):'';}catch{return '';}};
const escape=v=>clean(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const phrases={
 'Completed activities':'Atividades realizadas','Pending work and next steps':'Trabalho pendente e próximos passos','Supporting evidence':'Evidências complementares','Original records appendix':'Anexo de registros originais','Historical records may describe earlier conditions; current status is shown above.':'Os registros históricos podem descrever situações anteriores; a situação atual está apresentada acima.','Representative photo; full album in the complete report.':'Foto representativa; álbum completo no relatório completo.','No photo recorded for this activity.':'Nenhuma foto registrada para esta atividade.','Shared evidence':'Evidência compartilhada','Recorded completion':'Conclusão registrada','Additional planning instructions':'Orientações de planejamento','Return preparation':'Preparação do retorno',

 'Unit report':'Relatório da unidade','Summary':'Resumido','Complete':'Completo',
 'Current situation':'Situação atual','Work performed':'Trabalho realizado','Findings':'Conclusão / constatações',
 'Pending items':'Pendências','Initial conditions and scope':'Condições iniciais e escopo',
 'Initial conditions':'Condições iniciais','Work scope':'Escopo do trabalho','Next steps':'Próximos passos',
 'Action':'Ação','Status':'Situação','Responsible':'Responsável','Date':'Data',
 'Technical reference':'Referência técnica','Equipment':'Equipamento','Model':'Modelo',
 'Supply':'Alimentação','MCA':'MCA','Maximum overcurrent protection':'Proteção máxima contra sobrecorrente',
 'Disconnect rating':'Capacidade do disconnect','Source / verification':'Origem / verificação',
 'Nameplate':'Placa do equipamento','Verified circuit':'Circuito verificado','Not specified':'Não especificado',
 'Not recorded':'Não informado','Not assigned':'Não atribuído','Not scheduled':'Sem data definida',
 'Return':'Retorno','Unit coordinator':'Responsável pelo acompanhamento','Preparation':'Preparação',
 'Access':'Acesso','Materials':'Materiais','Team':'Equipe','Ready':'Pronto','Pending':'Pendente',
 'Completed':'Concluído','Not applicable':'Não se aplica','Required':'Necessário','Not required':'Não necessário',
 'Recorded tasks':'Tarefas registradas','Completed tasks':'Tarefas concluídas','Pending tasks':'Tarefas pendentes',
 'Field records':'Registros de campo','Evidence':'Evidências','Photo':'Foto','Photos':'Fotos','Video':'Vídeo','Audio':'Áudio',
 'Open original':'Abrir original','Saved evidence':'Evidência registrada','Full field history':'Histórico completo de campo',
 'Task register':'Registro de tarefas','Purchase lists':'Listas de compras','Quantity':'Quantidade','Unit':'Unidade',
 'Code':'Código','Item':'Item','Purchased':'Comprado','To purchase':'A comprar',
 'Unverified technical values must not be treated as installed circuit specifications.':'Valores técnicos não verificados não devem ser tratados como especificações do circuito instalado.',
 'No structured technical reference recorded. See the complete field history.':'Nenhuma referência técnica estruturada registrada. Consulte o histórico completo de campo.',
 'See the complete report for the recorded scope.':'Consulte o relatório completo para o escopo registrado.',
 'No work completion recorded in the task register.':'Nenhuma conclusão de tarefa registrada.',
 'No next action recorded.':'Nenhuma próxima ação registrada.',
 'Some descriptions have no reviewed translation and remain in their original language.':'Algumas descrições não têm tradução revisada e permanecem no idioma original.',
 'Additional evidence is available in the complete report.':'Outras evidências estão disponíveis no relatório completo.',
 'Initial assessment':'Avaliação inicial','Observed conditions':'Condições identificadas','Scope update':'Atualização do escopo',
 'Items to verify':'Itens a verificar','General observation':'Observação geral','Before installation':'Antes da instalação',
 'During work':'Durante o trabalho','After completion':'Após a conclusão','After installation':'Após a instalação',
 'Task progress':'Progresso das tarefas','Progress does not include unrecorded investigation or work.':'O progresso considera apenas as tarefas registradas.',
 'Snapshot generated':'Relatório gerado','HVAC equipment 1':'Máquina de ar-condicionado 1','HVAC equipment 2':'Máquina de ar-condicionado 2','No evidence recorded':'Nenhuma evidência registrada',
 'No purchase list linked to this unit.':'Nenhuma lista de compras vinculada à unidade.',
 'Record brief, reviewed summaries in Unit follow-up. Original field records remain in the complete report.':'Registre resumos curtos e revisados em Unit follow-up. Os registros originais permanecem no relatório completo.'
};
export const reportSummaryKeys=['initialConditions','workScope','workDone','findings','pending'];
export const equipmentKeys=['name','model','supply','mca','maxProtection','disconnect','source'];
export function normalizeReportSummary(v={}){return Object.fromEntries(reportSummaryKeys.map(k=>[k,clean(v?.[k])]));}
export function normalizeEquipment(v=[]){return (Array.isArray(v)?v:[]).filter(r=>r&&typeof r==='object').map(r=>Object.fromEntries(equipmentKeys.map(k=>[k,k==='source'?(['nameplate','circuit'].includes(r[k])?r[k]:''):clean(r[k])]))).filter(r=>equipmentKeys.some(k=>r[k]));}
function dateValue(v){if(!v)return '';if(v.toDate)return v.toDate().toISOString();return clean(v);}
function dateLabel(v,language){const value=dateValue(v);if(!value)return '';const date=new Date(/^\d{4}-\d{2}-\d{2}$/.test(value)?value+'T12:00:00':value);return isNaN(date)?value:date.toLocaleDateString(language==='pt'?'pt-BR':'en-US',{timeZone:'America/New_York'});}
export function collectUnitEvidence(room,notes,tasks,evidenceRows){
 const result=[],seen=new Set();
 const add=(record,phase,label)=>{for(const row of evidenceRows(record)||[]){if(!safeURL(row.url)||seen.has(row.url))continue;seen.add(row.url);result.push({...row,phase,label});}};
 add({photoUrl:room.photos?.before,photos:[...(room.scopeBrief?.photos||[]),...(room.initialObservationPhotos||[])],attachments:room.scopeBrief?.attachments||[]},'before-installation','Initial conditions');
 add({photoUrl:room.photos?.after},'after-completion','Completed tasks');
 for(const n of notes)add(n,n.phase||'general','Field records');
 for(const t of tasks)add({photos:t.photos||[]},t.done?'after-completion':'during-work',t.name||'Recorded tasks');
 return result;
}
export function buildUnitReport(room,state,{language='en',mode='summary',includeHistory=false,author=()=>'',evidenceRows=()=>[],now=new Date()}={}){
 language=language==='pt'?'pt':'en';mode=mode==='complete'?'complete':'summary';
 const L=s=>language==='pt'?(phrases[s]||translateText(s,'pt')):s;
 let untranslated=false;
 const narrative=v=>{const source=clean(v);if(!source)return escape(L('Not recorded'));const translated=language==='pt'?translateText(source,'pt'):source;if(language==='pt'&&!translations.has(source.replace(/\r/g,'').replace(/[ \t]+/g,' '))&&source.split('\n').some(line=>line.trim()&&translateText(line,'pt')===line&&/[a-z]/i.test(line)&&!/[ãõçáéíóúâêô]/i.test(line)))untranslated=true;return escape(translated).replace(/\n/g,'<br>');};
 const keep=v=>'<span data-report-keep-original>'+escape(clean(v)||L('Not recorded'))+'</span>';
 const tasks=Object.values(state.tasks||{}).filter(t=>t.roomId===room.id&&(!t.projectId||t.projectId===room.projectId));
 const completed=tasks.filter(t=>t.done).sort((a,b)=>(a.reportOrder??999)-(b.reportOrder??999)||dateValue(a.workDate||a.doneAt).localeCompare(dateValue(b.workDate||b.doneAt))),pending=tasks.filter(t=>!t.done),p=room.followUp||{},summary=normalizeReportSummary(p.reportSummary),equipment=normalizeEquipment(p.equipment);
 const notes=Object.entries(state.notes||{}).map(([id,n])=>({...n,id:n.id||id})).filter(n=>n.roomId===room.id&&(!n.projectId||n.projectId===room.projectId)).sort((a,b)=>{const left=Date.parse(dateValue(a.savedAt||a.createdAt))||0,right=Date.parse(dateValue(b.savedAt||b.createdAt))||0;return left-right||a.id.localeCompare(b.id);});
 const project=state.projects?.[room.projectId]||{},evidence=collectUnitEvidence(room,notes,tasks,evidenceRows),scope=room.scopeBrief||{};
 const section=(key,title,body)=>'<section class="ur-section" data-report-section="'+key+'"><h2>'+escape(L(title))+'</h2>'+body+'</section>';
 const value=(title,v)=>'<div class="ur-fact">'+(title?'<h3>'+escape(L(title))+'</h3>':'')+'<div class="ur-value">'+v+'</div></div>';
 const steps=clean(p.nextStep||scope.nextStep).split(/\n+/).map(s=>s.trim()).filter(Boolean);
 const assigned=(id)=>id?author(id)||id:L('Not assigned');
 const returnDate=p.returnDate?dateLabel(p.returnDate,language)+(p.returnTime?' · '+escape(p.returnTime):''):p.returnNeeded==='no'?L('Not required'):p.returnNeeded==='yes'?L('Required')+' · '+L('Not scheduled'):L('Not specified');
 const progress=tasks.length?Math.round(completed.length/tasks.length*100):null;
 let html='<article class="ur-report"><header class="ur-header"><div><div class="ur-brand">OBRA MANAGER</div><div class="rpt-proj">'+keep(project.name)+'</div>'+(project.address?'<div class="ur-muted">'+keep(project.address)+'</div>':'')+'<h1>'+keep(room.name)+' · '+escape(L('Unit report'))+'</h1></div><div class="ur-meta">'+escape(L(mode==='complete'?'Complete':'Summary'))+'<br>'+escape(dateLabel(now.toISOString(),language))+'</div></header>';
 html+='<div class="ur-metrics"><span>'+escape(L('Completed tasks'))+': <b>'+completed.length+'</b></span><span>'+escape(L('Pending tasks'))+': <b>'+pending.length+'</b></span><span>'+escape(L('Task progress'))+': <b>'+(progress===null?'—':progress+'%')+'</b></span></div>';
 const table=(headers,rows)=>'<div class="ur-table-wrap"><table><thead><tr>'+headers.map(h=>'<th>'+escape(L(h))+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(cell=>'<td>'+cell+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 const usedPictures=new Set(),claimedPictures=new Set(),usedMedia=new Set();
 const gallery=rows=>'<div class="ur-gallery">'+rows.map(r=>'<figure><a href="'+escape(r.url)+'" target="_blank" rel="noopener"><img src="'+escape(r.url)+'" alt="'+escape(L('Saved evidence'))+'" loading="eager"></a><figcaption>'+keep(r.name||L('Photo'))+'</figcaption></figure>').join('')+'</div>';
 const mediaLinks=rows=>'<ul class="ur-media">'+rows.map(r=>'<li><a href="'+escape(r.url)+'" target="_blank" rel="noopener">'+escape(L(r.type==='video'?'Video':'Audio'))+' · '+escape(r.name||L('Open original'))+'</a></li>').join('')+'</ul>';
 html+=section('overview','Current situation','<div class="ur-status">'+narrative(p.status)+'</div>'+(summary.findings?value('Findings',narrative(summary.findings)):''));
 html+=section('scope','Initial conditions and scope','<div class="ur-two-column">'+value('Initial conditions',narrative(summary.initialConditions||scope.before))+value('Work scope',narrative(summary.workScope||scope.workScope))+'</div>');
 const activityRows=completed.map(t=>{
  const rows=(evidenceRows(t)||[]).filter(r=>safeURL(r.url));
  for(const nid of t.reportEvidenceNoteIds||[]){const n=notes.find(n=>n.id===nid);if(n)rows.push(...(evidenceRows(n)||[]).filter(r=>safeURL(r.url)&&r.type!=='image'));}
  const pictures=rows.filter((r,i)=>r.type==='image'&&rows.findIndex(x=>x.url===r.url)===i),fresh=pictures.filter(r=>!usedPictures.has(r.url)),shown=mode==='complete'?fresh:fresh.slice(0,1);
  pictures.forEach(r=>claimedPictures.add(r.url));shown.forEach(r=>usedPictures.add(r.url));
  const media=rows.filter((r,i)=>r.type!=='image'&&!usedMedia.has(r.url)&&rows.findIndex(x=>x.url===r.url)===i);media.forEach(r=>usedMedia.add(r.url));
  const dates=dateLabel(t.workDate||t.doneAt,language);
  return '<article class="ur-activity" data-report-task="'+escape(t.id||'')+'"><header><h3>'+narrative(t.name)+'</h3><span class="ur-badge">'+escape(L('Completed'))+(dates?' · '+escape(dates):'')+'</span></header>'+((t.reportBrief||mode==='complete'&&t.note)?'<p>'+narrative(t.reportBrief||t.note)+'</p>':'')+(shown.length?gallery(shown):pictures.length?'<p class="ur-muted">'+escape(L('Shared evidence'))+': '+pictures.map(r=>'<a href="'+escape(r.url)+'" target="_blank" rel="noopener">'+escape(r.name||L('Photo'))+'</a>').join(' · ')+'</p>':'<p class="ur-muted">'+escape(L('No photo recorded for this activity.'))+'</p>')+(media.length?mediaLinks(media):'')+(mode==='summary'&&pictures.length>shown.length?'<p class="ur-muted">'+escape(L('Representative photo; full album in the complete report.'))+' ('+pictures.length+' '+escape(L('Photos'))+')</p>':'')+'</article>';
 });
 html+=section('completed','Completed activities',activityRows.length?activityRows.join(''):value('Work performed',summary.workDone?narrative(summary.workDone):escape(L('No work completion recorded in the task register.'))+' '+escape(L('Field records'))+': '+notes.length));
 const actionRows=pending.map(t=>[narrative(t.name),escape(L('Pending')),keep(assigned(t.assignedTo)),escape(t.assignedDate?dateLabel(t.assignedDate,language):L('Not scheduled'))]);
 html+=section('actions','Pending work and next steps',(summary.pending?value('Pending items',narrative(summary.pending)):'')+(actionRows.length?table(['Action','Status','Responsible','Date'],actionRows):'<p>'+escape(L('No next action recorded.'))+'</p>')+((!pending.length||mode==='complete')&&steps.length?value('Additional planning instructions','<ul>'+steps.map(s=>'<li>'+narrative(s)+'</li>').join('')+'</ul>'):''));
 const prep=Object.entries({access:'Access',materials:'Materials',team:'Team'}).filter(([k])=>p.preparation?.[k]).map(([k,label])=>escape(L(label))+': '+escape(L({yes:'Ready',no:'Pending',na:'Not applicable'}[p.preparation[k]]||'Not specified'))).join(' · ');
 html+=section('technical','Technical reference',equipment.length?table(['Equipment','Model','Supply','MCA','Maximum overcurrent protection','Disconnect rating','Source / verification'],equipment.map(r=>[keep(L(r.name)),keep(r.model),keep(r.supply),keep(r.mca),keep(r.maxProtection),keep(r.disconnect),escape(L(r.source==='nameplate'?'Nameplate':r.source==='circuit'?'Verified circuit':'Not specified'))]))+'<p class="ur-muted">'+escape(L('Unverified technical values must not be treated as installed circuit specifications.'))+'</p>':'<p>'+escape(L('No structured technical reference recorded. See the complete field history.'))+'</p>');
 const lists=Object.values(state.lists||{}).filter(l=>l.projectId===room.projectId&&l.listType!=='template'&&((p.listIds||[]).includes(l.id)||Object.values(state.items||{}).some(i=>i.listId===l.id&&i.roomId===room.id)));
 html+=section('purchases','Purchase lists',lists.length?lists.map(l=>{const items=Object.values(state.items||{}).filter(i=>i.listId===l.id&&((p.listIds||[]).includes(l.id)||i.roomId===room.id));if(mode==='summary')return '<p>'+keep(l.name)+' · '+escape(L('To purchase'))+': '+items.filter(i=>!i.bought).length+'</p>';return '<h3>'+keep(l.name)+'</h3>'+table(['Code','Item','Quantity','Unit','Status'],items.map(i=>[keep(i.code||i.materialCode),keep(i.name||i.description),keep(i.qty??i.quantity),keep(i.unit),escape(L(i.bought?'Purchased':'To purchase'))]));}).join(''):'<p>'+escape(L('No purchase list linked to this unit.'))+'</p>');
 html+=section('planning','Return preparation','<div class="ur-two-column">'+value('Return',escape(returnDate))+value('Unit coordinator',keep(p.responsibleId?assigned(p.responsibleId):L('Not assigned')))+'</div>'+(prep?'<p>'+prep+'</p>':'')+(p.accessNote?value('Access',narrative(p.accessNote)):''));
 const pictures=evidence.filter(r=>r.type==='image'&&!claimedPictures.has(r.url)),selected=mode==='complete'?pictures:[...new Set(pictures.map(r=>r.phase))].slice(0,2).map(phase=>pictures.find(r=>r.phase===phase));
 const media=evidence.filter(r=>r.type!=='image'&&!usedMedia.has(r.url));
 html+=section('evidence','Supporting evidence',(selected.length?gallery(selected):'<p class="ur-muted">'+escape(L('No evidence recorded'))+'</p>')+(media.length?mediaLinks(media):'')+(mode==='summary'&&evidence.filter(r=>r.type==='image').length>usedPictures.size+selected.length?'<p class="ur-muted">'+escape(L('Additional evidence is available in the complete report.'))+' ('+evidence.filter(r=>r.type==='image').length+' '+escape(L('Photos'))+')</p>':''));
 if(mode==='complete'&&includeHistory){
  html+=section('archive','Original records appendix','<p class="ur-muted">'+escape(L('Historical records may describe earlier conditions; current status is shown above.'))+'</p>');

  html+=section('assessment','Initial assessment',['initialAnalysis','before','difficulties','impact','nextStep','workScope','observations'].filter(k=>scope[k]).map(k=>value({initialAnalysis:'Initial assessment',before:'Initial conditions',difficulties:'Observed conditions',impact:'Scope update',nextStep:'Next steps',workScope:'Work scope',observations:'Items to verify'}[k],narrative(scope[k]))).join('')||'<p>'+escape(L('Not recorded'))+'</p>');
  html+=section('history','Full field history',notes.length?notes.map(n=>'<div class="ur-record"><h3>'+escape(L({'before-installation':'Before installation','during-work':'During work','after-completion':'After completion','after-installation':'After installation'}[n.phase]||'General observation'))+'</h3><p class="ur-muted">'+escape(dateLabel(n.savedAt||n.createdAt,language))+' · '+keep(n.createdBy?author(n.createdBy)||n.createdBy:L('Not assigned'))+'</p>'+value('Field records',narrative(n.text||n.transcript))+[n.difficulties&&value('Observed conditions',narrative(n.difficulties)),n.impact&&value('Scope update',narrative(n.impact)),n.nextStep&&value('Next steps',narrative(n.nextStep))].filter(Boolean).join('')+'</div>').join(''):'<p>'+escape(L('Not recorded'))+'</p>');
 }
 if(untranslated&&language==='pt')html='<p class="ur-language-note" role="note">'+escape(L('Some descriptions have no reviewed translation and remain in their original language.'))+'</p>'+html;
 return html+'<footer class="ur-footer">OBRA MANAGER · '+keep(room.name)+' · '+escape(L('Snapshot generated'))+' '+escape(dateLabel(now.toISOString(),language))+'</footer></article>';
}
export const reportStyles=`.ur-two-column{display:grid;grid-template-columns:1fr 1fr;gap:12px}.ur-status{padding:10px 12px;background:#fff6e1;border-left:3px solid #dfa128;border-radius:4px}.ur-activity{border:1px solid #dce3e8;border-radius:8px;padding:10px;margin:8px 0;break-inside:avoid}.ur-activity header{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:5px}.ur-activity h3{font-size:12px!important;margin:0!important}.ur-badge{font-size:9px;white-space:nowrap;background:#e8f4ed;color:#17653b;border-radius:4px;padding:3px 6px}.ur-activity .ur-gallery{margin-top:7px;grid-template-columns:repeat(4,minmax(0,1fr))}.ur-activity .ur-gallery img{height:100px}.ur-activity .ur-gallery figure{max-width:190px}.ur-report ol{padding-left:18px}.ur-media{font-size:10px}@media(max-width:520px){.ur-two-column{grid-template-columns:1fr}.ur-activity header{flex-wrap:wrap}.ur-activity .ur-gallery{grid-template-columns:repeat(2,minmax(0,1fr))}}.ur-report{color:#17212b;font-size:12px;line-height:1.45}.ur-report *{box-sizing:border-box}.ur-header{display:flex;justify-content:space-between;gap:12px;border-bottom:2px solid #dfa128;padding-bottom:10px;margin-bottom:12px}.ur-brand{font-weight:800;letter-spacing:1px;font-size:13px}.ur-header h1{font-size:21px;margin:7px 0 0}.ur-meta,.ur-muted{font-size:10px;color:#536171}.ur-meta{text-align:right;white-space:nowrap}.ur-metrics{display:flex;flex-wrap:wrap;gap:8px 20px;background:#f3f5f7;padding:8px 12px;border-radius:6px}.ur-section{margin:14px 0}.ur-section h2{font-size:14px;padding-bottom:5px;border-bottom:1px solid #d9dfe5;margin:0 0 8px;break-after:avoid}.ur-fact h3,.ur-report h3{font-size:11px;margin:6px 0 2px}.ur-fact p,.ur-section p{margin:3px 0 7px;overflow-wrap:anywhere}.ur-report ul{margin:4px 0;padding-left:18px}.ur-report li{margin:2px 0}.ur-table-wrap{max-width:100%;overflow-x:auto}.ur-report table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:10px}.ur-report th{background:#f0f3f6;font-weight:700;text-align:left}.ur-report th,.ur-report td{padding:6px;border:1px solid #dde2e7;vertical-align:top;overflow-wrap:anywhere}.ur-report tr{break-inside:avoid}[data-report-section=actions] th:first-child,[data-report-section=tasks] th:first-child{width:55%}[data-report-section=technical] th:nth-child(1){width:15%}[data-report-section=technical] th:nth-child(2){width:18%}[data-report-section=technical] th:nth-child(3){width:19%}[data-report-section=technical] th:nth-child(4){width:8%}.ur-value{overflow-wrap:anywhere}.ur-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.ur-gallery figure{margin:0;break-inside:avoid}.ur-gallery img{width:100%;height:110px;object-fit:contain;background:#f6f7f8;border:1px solid #e2e5e8}.ur-gallery figcaption{font-size:9px;color:#536171;overflow-wrap:anywhere}.ur-record{margin:12px 0;padding-top:8px;border-top:1px solid #ddd}.ur-footer{margin-top:16px;border-top:1px solid #ddd;padding-top:6px;font-size:9px;color:#536171}.ur-language-note{font-size:10px;color:#536171}.ur-report a{color:#174e7a}@media(max-width:520px){.ur-header{flex-wrap:wrap}.ur-meta{text-align:left}.ur-gallery{grid-template-columns:repeat(2,minmax(0,1fr))}.ur-report table{font-size:9px}.ur-report th,.ur-report td{padding:4px}}@media print{.ur-report{font-size:10px}.ur-section{margin:10px 0}.ur-report h2{font-size:12px}.ur-table-wrap{overflow:visible}.ur-header,.ur-fact,.ur-metrics{break-inside:avoid}.ur-gallery img{height:90px}.ur-footer{position:static}@page{size:A4;margin:10mm}}`;
export function installUnitReportStructure(host){
 let currentUnit=null;
 const select=document.getElementById('unit-report-format'),control=document.getElementById('unit-report-format-control'),archive=document.getElementById('unit-report-history'),archiveControl=document.getElementById('unit-report-history-control');
 if(!document.getElementById('unit-report-structure-style')){const style=document.createElement('style');style.id='unit-report-structure-style';style.textContent=reportStyles;document.head.append(style);}
 const bar=document.querySelector('#pdf-report .pdf-topbar');if(bar&&typeof ResizeObserver!=='undefined')new ResizeObserver(()=>{if(currentUnit)document.getElementById('pdf-report').style.paddingTop=(bar.getBoundingClientRect().height+8)+'px';}).observe(bar);
 const oldReset=window.unitReportLanguage?.reset;
 if(window.unitReportLanguage)window.unitReportLanguage.reset=()=>{currentUnit=null;if(control)control.hidden=true;if(archiveControl)archiveControl.hidden=true;if(archive)archive.checked=false;oldReset?.();};
 function generate(rid,language='en',mode,includeHistory){const state=host.state(),room=state.rooms?.[rid];if(!room)return;const same=currentUnit===rid;mode=mode|| (same?select?.value:'summary')||'summary';if(archive&&includeHistory!==undefined)archive.checked=!!includeHistory;else if(archive&&!same)archive.checked=false;if(archiveControl)archiveControl.hidden=mode!=='complete';currentUnit=rid;if(control)control.hidden=false;if(select)select.value=mode;const bar=document.querySelector('#pdf-report .pdf-topbar');if(bar)document.getElementById('pdf-report').style.paddingTop=(bar.getBoundingClientRect().height+8)+'px';
  const html=buildUnitReport({...room,id:rid},state,{language,mode,includeHistory:archive?.checked||false,author:host.author,evidenceRows:host.evidenceRows});
  // Let the existing language controller track the unit and print language; content is already localized.
  window.unitReportLanguage?.render('',language,rid);
  const content=document.getElementById('pdf-content');content.lang=language==='pt'?'pt-BR':'en';content.innerHTML=html;document.getElementById('pdf-report').classList.add('open');
 }
 select?.addEventListener('change',()=>{if(currentUnit)generate(currentUnit,document.getElementById('unit-report-language')?.value||'en',select.value);});
 archive?.addEventListener('change',()=>{if(currentUnit)generate(currentUnit,document.getElementById('unit-report-language')?.value||'en',select.value);});
 window.unitReportEngine={generate};return window.unitReportEngine;
}
