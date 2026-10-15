import {coverLabels,facadePhotoURL} from './photo-report-cover.js?v=1';
import {PDFDocument, StandardFonts, rgb} from './vendor/pdf-lib.esm.min.js';

const labels={
 en:{prepare:'Preparing PDF',ready:'PDF ready',share:'Share PDF',save:'Save PDF',open:'Open PDF',close:'Close',retry:'Try again',failed:'The PDF could not be completed. No partial file was saved.',missing:'Photos could not be loaded',page:'Page',of:'of',part:'Part',continued:'Continued',history:'Original field records',taskNotes:'Task notes',size:'pages',cancelled:'Cancelled'},
 pt:{prepare:'Preparando PDF',ready:'PDF pronto',share:'Compartilhar PDF',save:'Salvar PDF',open:'Abrir PDF',close:'Fechar',retry:'Tentar novamente',failed:'Não foi possível concluir o PDF. Nenhum arquivo incompleto foi salvo.',missing:'Fotos não carregadas',page:'Página',of:'de',part:'Parte',continued:'Continuação',history:'Registros originais de campo',taskNotes:'Notas das tarefas',size:'páginas',cancelled:'Cancelado'}
};
const dateLabel=(value,language)=>{try{return value?new Date(typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)?value+'T12:00:00':value).toLocaleDateString(language==='pt'?'pt-BR':'en-US',{year:'numeric',month:'short',day:'numeric'}):'';}catch{return String(value||'');}};
export const pdfFilename=name=>(String(name||'Report').replace(/[<>:"/\\|?*\x00-\x1f\x7f]/g,'-').replace(/[. ]+$/,'').trim()||'Report')+'.pdf';

export async function loadPhotoJPEG(url,signal){
 if(signal?.aborted)throw new DOMException('Cancelled','AbortError');
 const preview=Array.from(document.images||[]).find(img=>img.complete&&img.naturalWidth&&img.src===url&&img.crossOrigin==='anonymous');
 const image=preview||new Image();if(!preview)image.crossOrigin='anonymous';
 if(!preview)await new Promise((resolve,reject)=>{
  const cleanup=()=>{clearTimeout(timer);image.onload=image.onerror=null;signal?.removeEventListener('abort',abort);};
  const finish=error=>{cleanup();error?reject(error):resolve();};
  const abort=()=>{image.src='';finish(new DOMException('Cancelled','AbortError'));};
  const timer=setTimeout(()=>finish(new Error('Image loading timeout')),30000);
  image.onload=()=>finish();image.onerror=()=>finish(new Error('Image unavailable'));
  signal?.addEventListener('abort',abort,{once:true});image.src=url;
 });
 const scale=Math.min(1,1600/Math.max(image.naturalWidth,image.naturalHeight)),canvas=document.createElement('canvas');
 canvas.width=Math.max(1,Math.round(image.naturalWidth*scale));canvas.height=Math.max(1,Math.round(image.naturalHeight*scale));
 try{
  const context=canvas.getContext('2d');if(!context)throw new Error('Image conversion unavailable');
  context.fillStyle='#fff';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0,canvas.width,canvas.height);
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.8));if(!blob)throw new Error('Image conversion failed');
  return new Uint8Array(await blob.arrayBuffer());
 }finally{canvas.width=canvas.height=0;if(!preview)image.src='';}
}

export async function createPhotoReportPDF(model,options){
 const {language='en',includeHistory=false,strings:l,captionTitle,photoSheets,signal,onProgress=()=>{},loadImage=loadPhotoJPEG}=options;
 const ui=labels[language]||labels.en,pdf=await PDFDocument.create();
 pdf.setTitle(String(model.project.name||'Report'));pdf.setAuthor('Obra Manager');pdf.setSubject(l.title);pdf.setCreator('CrewNelo PDF export');
 const regular=await pdf.embedFont(StandardFonts.Helvetica),bold=await pdf.embedFont(StandardFonts.HelveticaBold);
 const supported=new Set(regular.getCharacterSet());
 const clean=value=>Array.from(String(value??'').replace(/\t/g,' ').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'')).map(c=>supported.has(c.codePointAt(0))||c==='\n'?c: /[\u200b-\u200f\ufe0f]/.test(c)?'':'?').join('');
 const ink=rgb(.09,.13,.17),muted=rgb(.32,.38,.43),gold=rgb(.7,.54,.2),line=rgb(.85,.88,.9),pale=rgb(.965,.972,.977);
 const W=612,H=792,M=36,BOTTOM=40,CW=W-M*2;let page,y;
 const wrap=(value,width,size=10,font=regular)=>{
  const lines=[];for(const paragraph of clean(value).split('\n')){
   let current='';for(const word of paragraph.split(/\s+/).filter(Boolean)){
    if(font.widthOfTextAtSize(current?(current+' '+word):word,size)<=width){current=current?current+' '+word:word;continue;}
    if(current){lines.push(current);current='';}
    let part='';for(const c of word){if(part&&font.widthOfTextAtSize(part+c,size)>width){lines.push(part);part='';}part+=c;}current=part;
   }lines.push(current);
  }return lines;
 };
 const text=(value,x,top,{size=10,font=regular,color=ink}={})=>page.drawText(clean(value),{x,y:top-size,size,font,color});
 const newPage=()=>{if(signal?.aborted)throw new DOMException('Cancelled','AbortError');page=pdf.addPage([W,H]);y=H-M;return page;};
 const projectHeader=()=>{for(const row of wrap(model.project.name,CW,9)){text(row,M,y,{size:9,color:muted});y-=12;}y-=7;};
 const flow=(value,{size=10,font=regular,color=ink,space=7}={})=>{
  for(const row of wrap(value,CW,size,font)){if(y-size*1.35<BOTTOM){newPage();projectHeader();}text(row,M,y,{size,font,color});y-=size*1.35;}y-=space;
 };
 const unitName=u=>u.room.unassigned?l.unassigned:u.service==='condensers'?l.condensers:u.room.name;
 const unitLabel=u=>u.service==='condensers'?unitName(u):l[u.service]+' · '+unitName(u);
 const groupHeader=(u,part,total)=>{
  newPage();page.drawRectangle({x:M,y:H-M-4,width:CW,height:3,color:gold});y-=17;
  projectHeader();
  for(const row of wrap(unitLabel(u),CW,16,bold)){text(row,M,y,{size:16,font:bold});y-=20;}
  const done=u.tasks.filter(t=>t.done).length,pending=u.tasks.length-done;
  flow([u.room.floor,u.photos.length+' '+l.photos,done+'/'+u.tasks.length+' '+l.complete,pending+' '+l.pending].filter(Boolean).join(' · '),{size:9,space:3});
  flow(ui.part+' '+part+' '+ui.of+' '+total,{size:9,color:muted,space:6});
 };
 const imageCache=new Map(),failures=[];let processed=0;
 const cover=coverLabels[language]||coverLabels.en,facadeURL=facadePhotoURL(model.project);
 newPage();
 // A dedicated cover keeps the facade and project identity together on page one.
 let titleSize=26,titleRows=wrap(model.project.name,CW-40,titleSize,bold);
 while(titleRows.length>3&&titleSize>12){titleSize--;titleRows=wrap(model.project.name,CW-40,titleSize,bold);}
 const address=model.project.address&&model.project.address!==model.project.name?model.project.address:'';
 const addressRows=address?wrap(address,CW-40,10):[];
 const headerHeight=100+titleRows.length*(titleSize+5)+addressRows.length*14,headerBottom=H-M-headerHeight;
 page.drawRectangle({x:M,y:headerBottom,width:CW,height:headerHeight,color:ink});
 page.drawRectangle({x:M,y:headerBottom,width:4,height:headerHeight,color:gold});
 text('OBRA MANAGER / FIELD DOCUMENTATION',M+20,H-M-17,{size:9,font:bold,color:rgb(.85,.73,.43)});
 text(l.title,M+20,H-M-39,{size:11,color:rgb(.82,.87,.9)});
 let titleY=H-M-65;
 for(const row of titleRows){text(row,M+20,titleY,{size:titleSize,font:bold,color:rgb(1,1,1)});titleY-=titleSize+5;}
 for(const row of addressRows){text(row,M+20,titleY-6,{size:10,color:rgb(.82,.87,.9)});titleY-=14;}
 const imageTop=headerBottom-18,imageHeight=Math.max(120,Math.min(facadeURL?310:210,imageTop-220));
 page.drawRectangle({x:M,y:imageTop-imageHeight,width:CW,height:imageHeight,color:pale,borderColor:line,borderWidth:.5});
 if(facadeURL){
  try{const embedded=await pdf.embedJpg(await loadImage(facadeURL,signal));imageCache.set(facadeURL,embedded);
   const scale=Math.min(CW/embedded.width,imageHeight/embedded.height),width=embedded.width*scale,height=embedded.height*scale;
   page.drawImage(embedded,{x:M+(CW-width)/2,y:imageTop-imageHeight+(imageHeight-height)/2,width,height});
  }catch(error){if(error.name==='AbortError')throw error;throw new Error(cover.failed);}
 }else{text(cover.overview,M+20,imageTop-35,{size:18,font:bold});text(cover.missing,M+20,imageTop-67,{size:10,color:muted});}
 text(facadeURL?cover.facade+' / '+cover.context:cover.overview,M,imageTop-imageHeight-8,{size:9,color:muted});
 y=imageTop-imageHeight-38;
 const stats=[[model.units.length,l.units],[model.totalPhotos,l.photos],[model.done,l.done],[model.pending,l.pending]],statGap=8,statWidth=(CW-statGap*3)/4;
 stats.forEach(([count,label],index)=>{const x=M+index*(statWidth+statGap);page.drawRectangle({x,y:y-63,width:statWidth,height:63,color:pale});text(count,x+10,y-7,{size:23,font:bold});wrap(label,statWidth-20,8).forEach((row,n)=>text(row,x+10,y-36-n*10,{size:8,color:muted}));});
 y-=82;flow(cover.issued+': '+dateLabel(new Date().toISOString(),language),{size:9,color:muted});
 // The index may continue naturally without crowding the cover.
 newPage();flow(l.contents,{size:20,font:bold,space:14});
 const filterRows=Object.entries(model.filters||{}).filter(([key,value])=>['floor','system','status','task','tech','units'].includes(key)&&value&&value!=='all'&&(!Array.isArray(value)||value.length));
 flow(l.filters+': '+(filterRows.map(([key,value])=>key+': '+(Array.isArray(value)?model.units.map(unitName).join(', '):value)).join(' · ')||l.all),{size:9,color:muted,space:12});
 flow(l.historical,{size:9,color:muted,space:18});
 model.units.forEach(u=>{flow(unitLabel(u)+' - '+u.photos.length+' '+l.photos,{size:10,space:5});});
 if(!model.units.length)flow(l.none);
 const totalImages=model.units.reduce((sum,u)=>sum+u.photos.length,0);
 // Keep at most three converted photos ahead of the layout, rather than waiting
 // for every network request in sequence or decoding the entire report at once.
 const urls=[...new Set(model.units.flatMap(u=>u.photos.map(p=>p.url)))].filter(url=>!imageCache.has(url)),pendingImages=new Map();let nextImage=0;
 const fillQueue=()=>{while(pendingImages.size<3&&nextImage<urls.length&&!signal?.aborted){const url=urls[nextImage++];pendingImages.set(url,Promise.resolve().then(()=>{if(signal?.aborted)throw new DOMException('Cancelled','AbortError');return loadImage(url,signal);}).then(bytes=>({bytes}),error=>({error})));}};
 fillQueue();
 for(const u of model.units){
  // Explicit PDF pages and measured cards do not depend on CSS grid fragmentation.
  const logical=photoSheets(u.photos,!includeHistory),sheets=[];
  logical.forEach(sheet=>{for(let i=0;i<sheet.length;i+=includeHistory?2:4)sheets.push(sheet.slice(i,i+(includeHistory?2:4)));});
  if(!sheets.length){groupHeader(u,1,1);flow(l.noPhotos);}
  for(let index=0;index<sheets.length;index++){
   groupHeader(u,index+1,sheets.length);const sheet=sheets[index],full=sheet.length===1&&sheet[0].fullPage;
   const columns=full||includeHistory?1:2,gap=12,cardWidth=(CW-gap*(columns-1))/columns;
   const cards=sheet.map(p=>{
    const ref=p.references.find(r=>r.source==='task')||p.references[0],stage=p.references.find(r=>r.stage&&r.stage!=='unspecified')?.stage;
    const meta=[ref?.status?l[ref.status]:l.history,ref?.date?dateLabel(ref.date,language):'',stage?l[stage]:''].filter(Boolean).join(' · ');
    const rows=[...wrap(l.photo+' '+p.number+' · '+unitName(u),cardWidth-4,9,bold).map(t=>({t,b:true})),...wrap(captionTitle(p),cardWidth-4,9).map(t=>({t})),...wrap(meta,cardWidth-4,8).map(t=>({t,m:true}))];
    return {p,rows,captionHeight:rows.reduce((h,r)=>h+(r.m?11:12),10)};
   });
   const rowCount=Math.ceil(cards.length/columns),rowGap=15,available=y-BOTTOM-10;
   const rowHeight=(available-rowGap*(rowCount-1))/rowCount,maxCaption=Math.max(...cards.map(c=>c.captionHeight));
   // Even unusually long captions get their own continuation page rather than clipping.
   const imageHeight=Math.max(64,Math.min(full?460:includeHistory?235:204,rowHeight-Math.min(maxCaption,95)));
   for(let n=0;n<cards.length;n++){
    const {p,rows}=cards[n],x=M+(n%columns)*(cardWidth+gap),top=y-Math.floor(n/columns)*(rowHeight+rowGap);
    let embedded=imageCache.get(p.url);
    if(!imageCache.has(p.url)){try{const loaded=await pendingImages.get(p.url);if(loaded.error)throw loaded.error;embedded=await pdf.embedJpg(loaded.bytes);imageCache.set(p.url,embedded);}catch(error){if(error.name==='AbortError')throw error;imageCache.set(p.url,null);failures.push(p.number);}finally{pendingImages.delete(p.url);fillQueue();}}
    if(embedded){const scale=Math.min(cardWidth/embedded.width,imageHeight/embedded.height);const width=embedded.width*scale,height=embedded.height*scale;page.drawRectangle({x,y:top-imageHeight,width:cardWidth,height:imageHeight,color:pale,borderColor:line,borderWidth:.5});page.drawImage(embedded,{x:x+(cardWidth-width)/2,y:top-imageHeight+(imageHeight-height)/2,width,height});}
    let captionY=top-imageHeight-6;const overflow=[];
    for(const row of rows){const step=row.m?11:12;if(captionY-step<top-rowHeight+4){overflow.push(row);continue;}text(row.t,x+2,captionY,{size:row.m?8:9,font:row.b?bold:regular,color:row.m?muted:ink});captionY-=step;}
    cards[n].overflow=overflow;processed++;onProgress(processed,totalImages);if(processed%4===0)await new Promise(resolve=>setTimeout(resolve,0));
   }
   for(const card of cards.filter(c=>c.overflow.length)){newPage();flow(unitLabel(u)+' · '+l.photo+' '+card.p.number+' · '+ui.continued,{size:14,font:bold});card.overflow.forEach(row=>flow(row.t,{size:row.m?8:9,font:row.b?bold:regular,space:2}));}
  }
  const pending=u.tasks.filter(t=>!t.done);
  if(pending.length){newPage();flow(unitLabel(u),{size:16,font:bold});flow(l.pending,{size:13,font:bold});pending.forEach(t=>flow('• '+t.name));}
 }
 if(failures.length)throw new Error(ui.missing+': '+failures.join(', '));
 if(includeHistory){
  newPage();flow(ui.history,{size:18,font:bold});
  model.units.forEach(u=>{
   flow(unitLabel(u),{size:14,font:bold,space:9});
   u.tasks.filter(t=>t.reportBrief||t.note).forEach(t=>{flow(t.name,{size:11,font:bold});flow(t.reportBrief||t.note);});
   u.notes.forEach((note,index)=>{flow(l.field+' '+(index+1)+' · '+dateLabel(note.createdAt||note.savedAt,language),{size:11,font:bold});flow([note.text,note.difficulties,note.impact,note.nextStep].filter(Boolean).join('\n'));const refs=u.photos.filter(p=>p.references.some(ref=>ref.source==='note'&&ref.sourceId===note.id));if(refs.length)flow(l.photos+': '+refs.map(p=>p.number).join(', '),{size:9,color:muted});});
  });
 }
 const pages=pdf.getPages();pages.forEach((p,index)=>{p.drawLine({start:{x:M,y:29},end:{x:W-M,y:29},color:line,thickness:.5});p.drawText(clean(ui.page+' '+(index+1)+' '+ui.of+' '+pages.length),{x:W-M-100,y:16,size:8,font:regular,color:muted});});
 const bytes=await pdf.save();return {bytes,pages:pages.length,photos:processed,filename:pdfFilename(model.project.name)};
}

let currentExport=null;
export function exportPhotoReportPDF(model,options){
 if(currentExport){currentExport.focus();return;}
 const language=options.language||'en',ui=labels[language]||labels.en,abort=new AbortController();let objectURL,file;
 const overlay=document.createElement('div');overlay.id='report-pdf-export';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label',ui.prepare);overlay.style.cssText='position:fixed;inset:0;z-index:20000;background:#0009;display:flex;align-items:center;justify-content:center;padding:20px;color:#17212b';
 const box=document.createElement('div');box.style.cssText='background:#fff;border-radius:14px;padding:24px;max-width:460px;width:100%;font:15px/1.5 Arial,sans-serif;max-height:90vh;overflow:auto';
 const heading=document.createElement('h2');heading.textContent=ui.prepare;heading.style.margin='0 0 8px';box.append(heading);
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent=model.project.name;box.append(status);
 const actions=document.createElement('div');actions.style.cssText='display:flex;gap:10px;flex-wrap:wrap';box.append(actions);
 const control=(label,run)=>{const b=document.createElement('button');b.textContent=label;b.style.cssText='min-height:44px;padding:10px 16px;border:1px solid #aab4bd;border-radius:8px;background:white;color:#17212b;font:inherit;cursor:pointer';b.onclick=run;actions.append(b);return b;};
 const progress=document.createElement('progress');progress.max=Math.max(1,model.totalPhotos);progress.value=0;progress.style.cssText='width:100%;height:12px;accent-color:#b38a33;margin:0 0 16px';progress.setAttribute('aria-label',ui.prepare);box.append(progress);
 const close=()=>{abort.abort();overlay.remove();if(objectURL)setTimeout(()=>URL.revokeObjectURL(objectURL),60000);currentExport=null;};
 const closeButton=control(ui.close,close);overlay.append(box);document.body.append(overlay);closeButton.focus();currentExport=closeButton;
 createPhotoReportPDF(model,{...options,signal:abort.signal,onProgress:(done,total)=>{progress.max=Math.max(1,total);progress.value=done;status.textContent=Math.round(done/Math.max(1,total)*100)+'% · '+done+' / '+total+' '+options.strings.photos;}}).then(result=>{
  if(abort.signal.aborted)return;file=new File([result.bytes],result.filename,{type:'application/pdf'});objectURL=URL.createObjectURL(file);
  progress.value=progress.max;heading.textContent=ui.ready;overlay.setAttribute('aria-label',ui.ready);status.textContent=result.filename+' · '+result.pages+' '+ui.size+' · '+(file.size/1048576).toFixed(1)+' MB';
  if(navigator.share&&navigator.canShare?.({files:[file]})){
   const share=control(ui.share,()=>{share.disabled=true;try{navigator.share({files:[file]}).catch(error=>{if(error.name!=='AbortError')status.textContent=error.message;}).finally(()=>{share.disabled=false;});}catch(error){share.disabled=false;status.textContent=error.message;}});actions.prepend(share);share.focus();
  }
  for(const [label,download] of [[ui.save,true],[ui.open,false]]){const link=document.createElement('a');link.textContent=label;link.href=objectURL;link.style.cssText=closeButton.style.cssText+';display:inline-block;text-decoration:none';if(download)link.download=result.filename;else{link.target='_blank';link.rel='noopener';}actions.insertBefore(link,closeButton);}
 }).catch(error=>{if(abort.signal.aborted)return;heading.textContent=ui.failed;status.textContent=error.message;control(ui.retry,()=>{close();exportPhotoReportPDF(model,options);});});
}
