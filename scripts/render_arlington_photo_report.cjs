const fs=require('node:fs'),assert=require('node:assert/strict');const {chromium}=require('playwright');
(async()=>{
 const input=JSON.parse(fs.readFileSync('tmp/photo-report/arlington-input.json','utf8'));
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{const u=new URL(route.request().url());if(u.hostname==='firebasestorage.googleapis.com')return route.continue();if(u.hostname!=='report.test')return route.abort();const path='public'+u.pathname;if(fs.existsSync(path)&&fs.statSync(path).isFile())return route.fulfill({contentType:'application/javascript',body:fs.readFileSync(path)});return route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><div id="pdf-report"><div id="pdf-content"></div></div></body></html>'});});
  await page.goto('https://report.test/test');
  const expected=await page.evaluate(async data=>{const m=await import('/photo-report.js');m.installPhotoReport();window.photoReport.open(data);return m.buildPhotoModel(data).totalPhotos;},input);
  assert(expected>=101,'The new report must preserve all 101 previously verified photos');
  await page.waitForFunction(()=>[...document.querySelectorAll('.pr-report img')].every(i=>i.complete),null,{timeout:120000});
  const audit=await page.locator('.pr-report').evaluate(el=>({photos:el.querySelectorAll('img').length,loaded:[...el.querySelectorAll('img')].filter(i=>i.naturalWidth>0).length,units:el.querySelectorAll('.pr-unit').length,historyShown:!!el.querySelector('.pr-history'),captionCharacters:[...el.querySelectorAll('figcaption')].map(c=>c.textContent.length),unitNames:[...el.querySelectorAll('.pr-unit h2')].map(h=>h.textContent)}));
  assert.equal(audit.loaded,audit.photos,'No missing evidence images');assert(!audit.historyShown,'Client report must not include the historical appendix by default');assert.equal(audit.units,12);assert(audit.captionCharacters.every(n=>n<550),'Photo captions must remain brief');
  const condensers=page.locator('.pr-unit').filter({has:page.getByRole('heading',{name:'Condensers',exact:true,level:2})});const captions=await condensers.locator('figcaption').allTextContents();assert(captions.some(t=>t.includes('7 Star Grocery')&&t.includes('20 A')));assert(captions.some(t=>t.includes('Backyartists')&&t.includes('30 A')));
  await page.emulateMedia({media:'print'});
  await page.pdf({path:'hosting-test/Arlington-photo-report-2.0.pdf',format:'Letter',printBackground:true,preferCSSPageSize:true});
  audit.uniquePhotos=expected;audit.runtimeErrors=errors;fs.writeFileSync('hosting-test/arlington-report-audit.json',JSON.stringify(audit,null,2));assert.deepEqual(errors,[]);
  console.log('ARLINGTON_REAL_REPORT_VERIFIED',JSON.stringify({units:audit.units,photos:audit.photos,loaded:audit.loaded,uniquePhotos:expected,historyShown:audit.historyShown,maxCaptionCharacters:Math.max(...audit.captionCharacters)}));
 }finally{await browser.close();fs.unlinkSync('tmp/photo-report/arlington-input.json');}
})().catch(e=>{console.error(e);process.exit(1)});
