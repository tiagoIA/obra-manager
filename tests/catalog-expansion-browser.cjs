const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),assert=require('node:assert/strict');
const {chromium}=require(require.resolve('playwright',{paths:[process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES||process.cwd()]}));
const root=process.cwd();
const data=JSON.parse(zlib.gunzipSync(fs.readFileSync('catalog-expansion/prepared-products.json.gz'))).materials;
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);return res.end();}
 res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':'text/plain');res.end(fs.readFileSync(file));
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  // Supplier images were checked separately; the UI test stays deterministic.
  await page.route('https://**/*',route=>route.abort());
  await page.goto('http://127.0.0.1:'+server.address().port+'/tests/library.html');
  await page.waitForFunction(()=>window.ready);
  await page.evaluate(rows=>{window.products=rows;window.library.render(document.getElementById('root'));},data);
  assert.equal(await page.locator('.mc-product').count(),24,'Catalog keeps a bounded first page with thousands of records');
  const search=page.getByRole('searchbox',{name:'Search materials'});
  for(const query of ['12-2','14-2','disjuntor Siemens','conector 1/2']){
   await search.fill(query);assert(await page.locator('.mc-product').count()>0,query+' finds imported source products');
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No mobile overflow');
  }
  const product=data.find(m=>m.brand==='Siemens'&&m.catalogFamily==='breakers');assert(product);
  await search.fill(product.manufacturerPart);assert(await page.locator('.mc-product').count()>0);
  await search.fill('');await page.setViewportSize({width:1440,height:1000});
  assert.equal(await page.locator('.mc-product').count(),24);
  assert.deepEqual(errors,[]);
  console.log('PASS real expansion dataset: '+data.length+' products, bounded rendering, mobile/desktop, wire sizes, synonyms and manufacturer-model search');
 }finally{await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
