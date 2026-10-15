const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(require.resolve('playwright',{paths:[process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES||process.cwd()]}));
const root=process.cwd();
const server=http.createServer((req,res)=>{let file=path.join(root,decodeURIComponent(req.url.split('?')[0]));if(req.url==='/')return res.end('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body></body></html>');if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}if(!fs.existsSync(file)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':file.endsWith('.png')?'image/png':'image/jpeg');res.end(fs.readFileSync(file));});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true});await page.goto('http://127.0.0.1:'+server.address().port+'/');
  const result=await page.evaluate(async()=>{
   const pdf=await import('/public/photo-report-pdf.js');const report=await import('/public/photo-report.js');
   let imageNames;try{const response=await fetch('/tmp/fixtures/images.json');if(!response.ok)throw Error('No local photos');imageNames=(await response.json()).map(name=>'/tmp/fixtures/'+name);}catch{imageNames=Array.from({length:6},(_,i)=>{const c=document.createElement('canvas');c.width=i%2?480:640;c.height=i%2?640:480;const ctx=c.getContext('2d');ctx.fillStyle=['#dde8f0','#e8e0d4','#d5e6d6'][i%3];ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#17212b';ctx.font='32px Arial';ctx.fillText('LAYOUT TEST '+i,40,80);ctx.strokeRect(20,20,c.width-40,c.height-40);return c.toDataURL('image/jpeg');});}
   const counts=[5,9,7,12,4,8,2,3,4,4,8,35];let seq=0;
   const model={project:{name:'Layout test — 101 photos',address:'Test fixture'},filters:{},totalPhotos:101,done:87,pending:0,units:counts.map((count,n)=>({room:{name:'Test unit '+(n+1),floor:'1st floor'},service:n===11?'condensers':'coax',tasks:Array.from({length:n===11?10:7},(_,i)=>({name:'Recorded task '+i,done:true})),notes:[],photos:Array.from({length:count},(_,i)=>({number:++seq,url:imageNames[(seq-1)%imageNames.length],references:[{source:'note',sourceId:'test-'+seq,description:i===0?'Location map — Test fixture.':'Recorded photo '+seq+' with a deliberately long caption to verify the card measurement keeps the complete description together with its photograph.',date:'2026-10-15',status:'complete',stage:'unspecified'}]}))}))};
   // Use the same locale that the application passes from its photo report.
   const strings={title:'Photographic work report 2.0',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',complete:'Completed',history:'Historical field records',historical:'Photo dates and field notes document their recorded conditions.',contents:'Contents',filters:'Applied filters',all:'Whole project',coax:'Coaxial cabling',condensers:'Condensers',photo:'Photo',field:'Field records',noPhotos:'No photos recorded for this unit.'};
   const options={strings,captionTitle:report.captionTitle,photoSheets:report.photoSheets};
   const summary=await pdf.createPhotoReportPDF(model,options);
   const completeModel={...model,units:[{...model.units[0],notes:[{id:'note',text:'Historical note '.repeat(600),createdAt:'2026-10-15'}]}],totalPhotos:5};
   const complete=await pdf.createPhotoReportPDF(completeModel,{...options,includeHistory:true});
   let refused=false;try{await pdf.createPhotoReportPDF({...model,units:[{...model.units[0],photos:model.units[0].photos.slice(0,1)}]},{...options,loadImage:()=>Promise.reject(new Error('Fixture unavailable'))});}catch{refused=true;}
   // The ready dialog contains actual PDF bytes and a named download, not an HTML print page.
   pdf.exportPhotoReportPDF({...model,units:[{...model.units[0],photos:model.units[0].photos.slice(0,1)}],totalPhotos:1},options);
   const b64=bytes=>{let out='';for(let i=0;i<bytes.length;i+=8192)out+=String.fromCharCode(...bytes.slice(i,i+8192));return btoa(out);};
   return {summary:{...summary,bytes:b64(summary.bytes)},complete:{...complete,bytes:b64(complete.bytes)},refused,filename:pdf.pdfFilename('455 Massachusetts Ave, Arlington, MA')};
  });
  assert.equal(result.summary.photos,101);assert.equal(result.refused,true);assert.equal(result.filename,'455 Massachusetts Ave, Arlington, MA.pdf');
  await page.getByRole('heading',{name:'PDF ready',exact:true}).waitFor();
  const save=page.getByRole('link',{name:'Save PDF',exact:true});assert.equal(await save.getAttribute('download'),'Layout test — 101 photos.pdf');
  fs.mkdirSync('tmp/pdfs',{recursive:true});for(const mode of ['summary','complete'])fs.writeFileSync('tmp/pdfs/'+mode+'.pdf',Buffer.from(result[mode].bytes,'base64'));
  await page.screenshot({path:'tmp/pdfs/pdf-ready-mobile.png'});
  const coverResult=await page.evaluate(async()=>{
   const report=await import('/public/photo-report.js'),pdf=await import('/public/photo-report-pdf.js');
   const canvas=document.createElement('canvas');canvas.width=900;canvas.height=600;const ctx=canvas.getContext('2d');ctx.fillStyle='#d8e3ec';ctx.fillRect(0,0,900,600);ctx.fillStyle='#efeee8';ctx.fillRect(220,200,460,340);ctx.fillStyle='#3c4f61';ctx.beginPath();ctx.moveTo(170,220);ctx.lineTo(450,60);ctx.lineTo(730,220);ctx.fill();ctx.fillStyle='#8a9fad';for(const x of [270,530]){ctx.fillRect(x,270,90,90);ctx.fillRect(x,400,90,90);}ctx.fillStyle='#6a5b47';ctx.fillRect(410,380,80,160);ctx.fillStyle='#17212b';ctx.font='20px Arial';ctx.fillText('FACADE LAYOUT TEST',20,580);const url=canvas.toDataURL('image/jpeg');
   const model={project:{name:'3 Bartlett Street',address:'Melrose, MA',facadePhoto:{url}},filters:{},units:[{room:{name:'Basement'},service:'general',tasks:[{name:'Install lighting circuit',done:true}],notes:[],photos:[{number:1,url,references:[{source:'task',sourceTitle:'Install lighting circuit',status:'complete'}]}]}],totalPhotos:1,done:1,pending:0};
   document.body.innerHTML='<style>'+report.photoReportCSS+'</style>'+report.renderPhotoReport(model);
   await document.querySelector('.pr-cover-photo img').decode();
   let loads=0;const result=await pdf.createPhotoReportPDF(model,{strings:{title:'Photographic work report 2.0',contents:'Contents',filters:'Applied filters',all:'Whole project',historical:'Recorded field conditions',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',general:'Units',complete:'Completed',photo:'Photo'},captionTitle:report.captionTitle,photoSheets:report.photoSheets,loadImage:async(...args)=>{loads++;return pdf.loadPhotoJPEG(...args);}});
   return {loads,photos:result.photos,pages:result.pages,overflow:document.documentElement.scrollWidth>innerWidth,coverPhotos:document.querySelectorAll('.pr-cover-photo img').length,workPhotos:document.querySelectorAll('.pr-gallery img').length,kpis:document.querySelectorAll('.pr-cover .pr-kpis>div').length,coverFont:getComputedStyle(document.querySelector('.pr-cover')).fontFamily};
  });
  assert.deepEqual(coverResult,{loads:1,photos:1,pages:3,overflow:false,coverPhotos:1,workPhotos:1,kpis:4,coverFont:'Arial, sans-serif'});
  await page.locator('.pr-cover').screenshot({path:'tmp/pdfs/cover-mobile.png'});await page.setViewportSize({width:1280,height:1000});await page.locator('.pr-cover').screenshot({path:'tmp/pdfs/cover-desktop.png'});
  console.log('PASS: facade preview on mobile/desktop, cached image reuse, exact evidence count, dedicated cover and index.');
  console.log(JSON.stringify({summary:{pages:result.summary.pages,photos:result.summary.photos},complete:{pages:result.complete.pages,photos:result.complete.photos},missingImageRefused:result.refused,downloadFilename:result.filename}));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
