const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const moduleCode=name=>{const raw=fs.readFileSync('public/'+name,'utf8'),names=[...raw.matchAll(/export (?:async )?(?:function|const) (\w+)/g)].map(m=>m[1]);return '(()=>{'+raw.replace(/^import .*;\n/gm,'').replace(/export /g,'')+';Object.assign(window,{'+names.join(',')+'});})();';};
(async()=>{
const fixture=JSON.parse(fs.readFileSync('tmp/guided-fire/fixture.json','utf8'));const browser=await chromium.launch({headless:true});
try{
const page=await browser.newPage({viewport:{width:1280,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('https://guided.test/**',r=>r.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body></body></html>'}));
await page.goto('https://guided.test/');
await page.addScriptTag({content:moduleCode('purchasing-core.js')+moduleCode('central-catalog-v1.js')+moduleCode('guided-shopping-v1.js')+
'const fixture='+JSON.stringify(fixture)+';installGuidedShopping({userId:()=>fixture.owner,projectId:()=>"",projects:()=>[],materials:()=>fixture.materials,templates:()=>[fixture.template],lists:()=>[],notify:()=>{},openMaterial:()=>{}});guidedShopping.launch();'});
await page.getByRole('button',{name:'✨ Guided list'}).click();
await page.getByLabel('Fire Alarm — Scope List',{exact:true}).check();
await page.getByRole('button',{name:'Choose materials →'}).click();
assert.equal(await page.locator('.gs-picked').count(),23);
for(const row of await page.locator('.gs-picked').all())await row.scrollIntoViewIfNeeded();
try{await page.waitForFunction(()=>[...document.querySelectorAll('.gs-picked img')].length===23&&[...document.querySelectorAll('.gs-picked img')].every(i=>i.complete&&i.naturalWidth>0),null,{timeout:30000});}catch(error){console.log('GUIDED_PHOTO_DIAGNOSTIC',JSON.stringify(await page.locator('.gs-picked').evaluateAll(rows=>rows.map(row=>({name:row.querySelector('.gs-name')?.textContent,photo:!!row.querySelector('img'),loaded:!!row.querySelector('img')?.naturalWidth,host:row.querySelector('img')?new URL(row.querySelector('img').src).hostname:null})).filter(i=>!i.loaded))));throw error;}
const draft=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('guided-shopping-v3:'+fixture.owner)));
assert.equal(draft.items.length,23);assert.deepEqual(draft.items.map(i=>i.sourceQty),[9,7,9,0,3,3,4,null,null,1,null,1,2,1,2,1,2,1,null,2,2,1,null]);
assert(draft.items[18].obs.includes('2 beacons'));assert(!draft.items[5].matId);
assert.equal(await page.locator('.gs-picked img').count(),23);assert.deepEqual(errors,[]);
fs.mkdirSync('guided-verification',{recursive:true});await page.screenshot({path:'guided-verification/fire-alarm-guided-list.png',fullPage:true});
console.log('GUIDED_UI_VERIFIED',JSON.stringify({name:draft.name,lines:draft.items.length,loadedPhotos:23,sourceQuantitiesPreserved:true,requiresReview:!draft.reviewed}));
}finally{await browser.close();fs.unlinkSync('tmp/guided-fire/fixture.json');}
})().catch(e=>{console.error(e);process.exitCode=1;});
