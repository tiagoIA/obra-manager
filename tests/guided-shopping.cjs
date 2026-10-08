const {chromium}=require('playwright');
const fs=require('fs');const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('http://guided.test/',r=>r.fulfill({contentType:'text/html',body:'<html><body><button id="launch">Nova lista</button><style>:root{--bg:#1A1C1E;--txt:#F4F3F0;--bdr:#444}input,select,textarea{padding:8px;box-sizing:border-box}button{padding:9px;margin:5px}body{font-family:Arial}</style></body></html>'}));await page.goto('http://guided.test/');
 await page.addScriptTag({content:fs.readFileSync('public/guided-shopping-v1.js','utf8').replaceAll('export ','')+`\nwindow.testSaved=[];window.testModels=[];installGuidedShopping({userId:()=> 'test-user',projectId:()=>'',projects:()=>[{id:'p1',name:'Obra teste'}],materials:()=>[{id:'m1',name:'Cabo de teste',sku:'TEST-1',unit:'ft',cat:'eletrica'}],templates:()=>[],list:()=>null,items:()=>[],notify:(m,t)=>window.testMessages=(window.testMessages||[]).concat({m,t}),saveTemplate:async m=>window.testModels.push(m),saveList:async d=>{window.testSaved.push(d);return 'test-list'},openList:id=>window.opened=id});document.getElementById('launch').onclick=()=>guidedShopping.launch();`});
 await page.getByText('Nova lista',{exact:true}).click();await page.getByRole('button',{name:'Lista Personalizada — começar vazia'}).click();
 await page.getByLabel('Nome da lista',{exact:true}).fill('Trabalho personalizado');await page.getByRole('button',{name:'+ Adicionar material',exact:true}).click();
 await page.getByLabel('Material',{exact:true}).fill('Item <script> personalizado');await page.getByLabel('Quantidade',{exact:true}).fill('3');await page.getByRole('button',{name:'Salvar como novo modelo',exact:true}).click();
 assert.equal(await page.evaluate(()=>testModels.length),1);await page.getByRole('button',{name:'Criar lista de compras',exact:true}).click();assert.equal(await page.evaluate(()=>testSaved.length),0);
 await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Criar lista de compras',exact:true}).click();assert.equal(await page.evaluate(()=>testSaved[0].items[0].name),'Item <script> personalizado');assert.equal(await page.evaluate(()=>opened),'test-list');
 await page.getByText('Nova lista',{exact:true}).click();await page.getByRole('button',{name:'Lista Guiada — usar modelos'}).click();assert.equal(await page.getByRole('checkbox').count(),10);
 await page.getByRole('checkbox').nth(0).check();await page.getByRole('checkbox').nth(2).check();await page.getByRole('button',{name:'Responder e revisar materiais'}).click();assert.equal(await page.getByLabel('Material',{exact:true}).count(),9);
 await page.getByRole('button',{name:'Remover material',exact:true}).first().click();assert.equal(await page.getByLabel('Material',{exact:true}).count(),8);
 await page.getByRole('button',{name:'Criar lista de compras',exact:true}).click();assert.equal(await page.evaluate(()=>testSaved.length),1);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);assert.deepEqual(errors,[]);
 await page.screenshot({path:'guided-mobile.png',fullPage:true});await browser.close();console.log('PASS: custom list, model save, review gate, 10 presets, combine, remove, unresolved quantities, mobile layout, no JS errors');
})().catch(e=>{console.error(e);process.exit(1)});
