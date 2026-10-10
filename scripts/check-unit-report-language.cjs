const fs=require('node:fs'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const source=fs.readFileSync('public/index.html','utf8');
const generator=source.slice(source.indexOf('window.generateUnitReport='),source.indexOf('window.generateReport='));
const printer=source.slice(source.indexOf('window.printPDF=function'),source.indexOf('window.shareWhatsApp='));
const topbar=source.slice(source.indexOf('<div id="pdf-report">'),source.indexOf('<div id="shop-pdf">'));
assert(source.includes("window.unitReportLanguage?.reset();"),'Project report resets unit-only controls');
const setup=`
import {installUnitReportLanguage,translations,translateText} from '/unit-report-language.js';
import {installUnitFollowup} from '/unit-followup.js';
import {installUnitReportStructure} from '/unit-report-structure.js';
window.rooms={roof:{id:'roof',name:'Roof',projectId:'p',floor:'Exterior',scopeBrief:{before:'HVAC units are already installed on the roof. The equipment supply circuits and the circuit for two outlets have already been brought to the roof.',photos:[{url:'/photo.svg'}]},followUp:{status:'Investigation completed; new panel-to-rooftop supply cable required; installation pending return.',nextStep:'1. Coordinate with store 06 to have the basement hatch and access route cleared before the return visit.',returnNeeded:'yes',preparation:{access:'no'},taskIds:['t']}}};
window.projects={p:{name:'Pending',address:'123 Main St'}};
window.allTasks={t:{id:'t',roomId:'roof',projectId:'p',name:'Install and connect 60 A HVAC disconnects',cat:'eletrica',done:false,photos:['/photo.svg']}};
window.roomNotesList={n:{roomId:'roof',phase:'before-installation',createdBy:'u',savedAt:'2026-10-09',text:[...translations.keys()].filter(k=>k.startsWith('Equipment 1:')||k.startsWith('Equipment 2:')||k.startsWith('These are equipment')).join('\\n\\n'),photoUrls:[{url:'/photo.svg'}],attachments:[{url:'/original.mp4',name:'original.mp4',type:'video'}]}};
window.x=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
window.phaseLabel=()=> 'BEFORE INSTALLATION';window.fieldAuthor=()=> 'Pending';
window.evidenceRows=n=>(n.photos||[]).map(p=>({...p,type:'image'}));
window.evidenceReport=()=>'<img src="/photo.svg" alt="Site evidence"><p><a href="/original.mp4">Video: original.mp4</a></p>';
installUnitFollowup({state:()=>({rooms,projects,tasks:allTasks,lists:{},items:{}}),author:fieldAuthor});
installUnitReportLanguage();
window.translations=translations;window.translateText=translateText;
${generator}
${printer}
installUnitReportStructure({state:()=>({rooms,projects,tasks:allTasks,notes:roomNotesList,lists:{},items:{}}),author:fieldAuthor,evidenceRows:n=>[...(n.photos||[]),...(n.photoUrls||[]),...(n.attachments||[])].map(p=>typeof p==='string'?{url:p,type:'image'}:{...p,type:p.type||'image'})});
window.generateUnitReport('roof','en','complete');`;
const fixture=`<!DOCTYPE html><html><head><meta charset="utf-8"><style>.pdf-topbar{display:flex;flex-wrap:wrap;gap:8px}#unit-report-language-control[hidden]{display:none!important}.pdf-page{max-width:900px;overflow-wrap:anywhere}img{max-width:100%}table{table-layout:fixed}</style></head><body>${topbar}<script type="module">${setup}</script></body></html>`;
const server=http.createServer((req,res)=>{if(req.url==='/'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fixture);}else if(req.url==='/photo.svg'){res.setHeader('Content-Type','image/svg+xml');res.end('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="40"><rect width="60" height="40" fill="blue"/></svg>');}else if(['/unit-report-language.js','/unit-followup.js','/unit-report-structure.js'].includes(req.url.split('?')[0])){res.setHeader('Content-Type','text/javascript');res.end(fs.readFileSync('public'+req.url.split('?')[0]));}else{res.statusCode=404;res.end();}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true});try{
 for(const width of [390,1280]){const page=await browser.newPage({viewport:{width,height:900}});const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error('Fixture page error:',e.message)});await page.goto('http://127.0.0.1:'+server.address().port);await page.waitForSelector('#pdf-report.open');
 const content=page.locator('#pdf-content'),language=page.getByLabel('PDF language / Idioma');
 assert.equal(await language.inputValue(),'en');assert((await content.innerText()).includes('Unit report'));
 const original=await content.innerHTML(),data=await page.evaluate(()=>JSON.stringify({rooms,allTasks,roomNotesList}));
 const media=await content.locator('img,a').evaluateAll(els=>els.map(e=>[e.tagName,e.getAttribute('src')||e.getAttribute('href')]));
 await language.selectOption('pt');const pt=await content.innerText();
 for(const t of ['Tarefas pendentes: 1','Relatório da unidade','Situação atual','Investigação concluída','Sem data definida','Antes da instalação','monofásica','Samsung AJ024BXS4CH/AA','26.0 A','30.0 A','18.3 A','20 A','disconnects de 60 A','Vídeo · original.mp4'])assert(pt.includes(t),t+'\n'+pt);
 assert(await page.evaluate(()=>translateText('✅ COMPLETED (2)','pt')==='✅ CONCLUÍDAS (2)'),'Completed section translates before generic badge');
 assert(!pt.includes('Some text'));assert(!pt.includes('Alguns textos'),'All fixture Roof explanations translated');
 assert.equal(await page.evaluate(()=>JSON.stringify({rooms,allTasks,roomNotesList})),data);
 assert.deepEqual(await content.locator('img,a').evaluateAll(els=>els.map(e=>[e.tagName,e.getAttribute('src')||e.getAttribute('href')])),media);
 assert.equal(await content.getAttribute('lang'),'pt-BR');assert.equal(await content.locator('.rpt-proj').innerText(),'Pending','Project name stays original');
 await page.evaluate(()=>{window.open=()=>({document:{write:html=>window.printedHTML=html,close:()=>{}}});window.printPDF();});
 assert((await page.evaluate(()=>printedHTML)).includes('<html lang="pt-BR">'));assert((await page.evaluate(()=>printedHTML)).includes('Investigação concluída'));
 await language.selectOption('en');assert.equal(await content.innerHTML(),original,'English restore is lossless');
 await language.selectOption('pt');assert.equal(await content.innerText(),pt,'Repeated switch is idempotent');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile report fits screen');
 const format=page.locator('#unit-report-format');await format.selectOption('summary');assert.equal(await format.inputValue(),'summary');assert.equal(await content.locator('[data-report-section=history]').count(),0);await language.selectOption('en');assert.equal(await format.inputValue(),'summary');await format.selectOption('complete');assert.equal(await content.innerHTML(),original);await page.evaluate(()=>{rooms.other={id:'other',name:'Other unit',projectId:'p'};generateUnitReport('other','pt');});assert.equal(await format.inputValue(),'summary','A different unit starts with the summary');assert.equal(await content.locator('[data-report-section]').count(),6);
 await page.evaluate(()=>{roomNotesList.n.text='<script>bad</script> New unreviewed observation.';generateUnitReport('roof','pt','complete');});
 assert((await content.innerText()).includes('permanecem no idioma original'));assert((await content.innerText()).includes('<script>bad</script>'));assert.equal(await content.locator('script').count(),0,'Narrative is escaped');
 await page.evaluate(()=>unitReportLanguage.reset());assert(!(await page.locator('#unit-report-language-control').isVisible()));assert.equal(await content.getAttribute('lang'),null);assert(!(await page.locator('#unit-report-format-control').isVisible()));
 assert.deepEqual(errors,[]);await page.close();
 }
 console.log('PASS: English default; Portuguese explanations, task/status/category labels; names/technical values/media preserved; print language; round trips; mobile/desktop; unknown original text; escaping; no record mutations; project report isolation.');
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
