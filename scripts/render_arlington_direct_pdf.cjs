const fs=require('node:fs'),assert=require('node:assert/strict');const {chromium}=require('playwright');
(async()=>{
 const input=JSON.parse(fs.readFileSync('tmp/photo-report/arlington-input.json','utf8'));
 const browser=await chromium.launch({headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1280,height:1000}});
 const cached=new Map();
 await page.route('**/*',async route=>{
 const u=new URL(route.request().url());
 if(u.hostname==='firebasestorage.googleapis.com'){
 if(!cached.has(u.href))cached.set(u.href,(async()=>{
 const response=await page.request.get(u.href);assert(response.ok(),'Evidence download failed');
 return {body:await response.body(),contentType:response.headers()['content-type']||'image/jpeg'};
 })());
 return route.fulfill({...await cached.get(u.href),headers:{'Access-Control-Allow-Origin':'*'}});
 }
 if(u.hostname!=='obra-manager-4ecc7.web.app')return route.abort();
 const path='public'+u.pathname;
 if(fs.existsSync(path)&&fs.statSync(path).isFile())return route.fulfill({contentType:'application/javascript',body:fs.readFileSync(path)});
 return route.fulfill({contentType:'text/html',body:'<!doctype html><html><body><div id="pdf-report"><div id="pdf-content"></div></div></body></html>'});
 });
 await page.goto('https://obra-manager-4ecc7.web.app/direct-report');
 const expected=await page.evaluate(async data=>{const m=await import('/photo-report.js');m.installPhotoReport();window.photoReport.open(data);return m.buildPhotoModel(data).totalPhotos;},input);
 assert(expected>=101);
 await page.waitForFunction(()=>[...document.querySelectorAll('.pr-report img')].every(i=>i.complete&&i.naturalWidth>0),null,{timeout:120000});
 const sources=await page.locator('.pr-report img').evaluateAll(imgs=>imgs.map(i=>i.src));
 const encoded=[];
 for(const url of sources){const asset=await cached.get(url);assert(asset);encoded.push('data:'+asset.contentType+';base64,'+asset.body.toString('base64'));}
 const audit=await page.evaluate(async encoded=>{
 const imgs=[...document.querySelectorAll('.pr-report img')];
 for(let j=0;j<imgs.length;j++){
 const original=new Image();original.src=encoded[j];await original.decode();
 const limit=imgs[j].closest('.pr-full')?1800:1280,scale=Math.min(1,limit/Math.max(original.naturalWidth,original.naturalHeight));
 const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(original.naturalWidth*scale));canvas.height=Math.max(1,Math.round(original.naturalHeight*scale));
 const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(original,0,0,canvas.width,canvas.height);
 imgs[j].src=canvas.toDataURL('image/jpeg',imgs[j].closest('.pr-full') ? .82 : .78);await imgs[j].decode();canvas.width=canvas.height=0;
 }
 return {photos:imgs.length,loaded:imgs.filter(i=>i.naturalWidth>0).length,units:document.querySelectorAll('.pr-unit').length,exportMethod:'direct-recovery'};
 },encoded);
 assert.equal(audit.photos,101);assert.equal(audit.loaded,101);assert.equal(audit.units,12);
 await page.emulateMedia({media:'print'});
 await page.pdf({path:'hosting-test/Arlington-resumido.pdf',format:'Letter',printBackground:true,preferCSSPageSize:true});
 audit.pdfBytes=fs.statSync('hosting-test/Arlington-resumido.pdf').size;
 fs.writeFileSync('hosting-test/arlington-direct-audit.json',JSON.stringify(audit,null,2));
 console.log('DIRECT_PDF_VERIFIED',JSON.stringify(audit));
 }finally{await browser.close();fs.unlinkSync('tmp/photo-report/arlington-input.json');}
})().catch(e=>{console.error(e);process.exit(1)});
