const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),vm=require('node:vm');
const {chromium}=require('playwright');
const root=process.cwd();
const server=http.createServer((req,res)=>{if(req.url==='/'){res.setHeader('Content-Type','text/html');return res.end('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body></body></html>');}const file=path.join(root,req.url.split('?')[0]);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':'text/plain');res.end(fs.readFileSync(file));});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:'+server.address().port+'/');
  const result=await page.evaluate(async()=>{
   const report=await import('/public/photo-report.js'),pdf=await import('/public/photo-report-pdf.js'),core=await import('/public/work-progress.js');
   const task=(n,d)=>({name:'Rework electrical circuit',done:false,subtasks:Array.from({length:n},(_,i)=>({done:i<d}))});
   const units=[{room:{name:'Basement',floor:'Basement'},tasks:[task(6,3),task(6,2),{name:'Secure and support all basement cables',done:true},...Array.from({length:4},()=>({name:'Remaining service',done:false}))]}, {room:{name:'Unit 1 - installation pending',floor:'1st Floor'},tasks:[{name:'Install receptacles',done:false}]},{room:{name:'EV Charger',floor:'Exterior'},tasks:[{name:'Test EV charger',done:true}]},{room:{name:'Field observations',floor:'Other'},tasks:[]}].map(u=>({...u,service:'general',notes:[],photos:[]}));
   const model={project:{name:'3 Bartlett Street',address:'Melrose, MA'},filters:{},units,totalPhotos:0,done:2,pending:7};
   window.progressModel=model;window.progressReport=report;
   document.body.innerHTML='<style>'+report.photoReportCSS+'</style>'+report.renderPhotoReport(model);
   const values=Array.from(document.querySelectorAll('.pr-unit-head [role=progressbar]'),e=>Number(e.getAttribute('aria-valuenow')));
   const strings={title:'Photographic work report 2.0',contents:'Contents',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',complete:'Completed',historical:'Recorded conditions',filters:'Applied filters',all:'Whole project',general:'Units',noPhotos:'No photos recorded'};
   const outputs={};for(const language of ['en','pt']){const result=await pdf.createPhotoReportPDF(model,{language,strings,captionTitle:report.captionTitle,photoSheets:report.photoSheets});outputs[language]=Array.from(result.bytes);}
   return {values,outputs,formula:[core.progressPercent([task(7,4)]),core.progressPercent([task(7,3)]),core.progressPercent(units[0].tasks)]};
  });
  assert.deepEqual(result.values,[26,0,100]);assert.deepEqual(result.formula,[57,43,26]);assert.deepEqual(errors,[]);
  fs.mkdirSync('tmp/pdfs',{recursive:true});for(const [lang,bytes] of Object.entries(result.outputs))fs.writeFileSync('tmp/pdfs/unit-progress-'+lang+'.pdf',Buffer.from(bytes));
  for(const language of ['en','pt']){
   await page.evaluate(lang=>{document.body.innerHTML='<style>'+progressReport.photoReportCSS+'</style>'+progressReport.renderPhotoReport(progressModel,lang);},language);
   for(const width of [390,1280]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Report overflow at '+width+' '+language);await page.locator('.pr-overview').screenshot({path:'tmp/pdfs/unit-progress-index-'+language+'-'+width+'.png'});if(language==='en')await page.locator('.pr-unit').first().screenshot({path:'tmp/pdfs/unit-progress-basement-'+width+'.png'});}
  }
  await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.locator('.pr-progress-fill').first().evaluate(e=>getComputedStyle(e).animationName),'none');
  await page.emulateMedia({media:'print',reducedMotion:'no-preference'});assert.equal(await page.locator('.pr-progress-fill').first().evaluate(e=>getComputedStyle(e).animationName),'none');
  // Ensure the report and the current application's progress formula agree.
  const html=fs.readFileSync('public/app.html','utf8'),source=html.match(/\/\/ BEGIN PARTIAL WORK PROGRESS([\s\S]*?)\/\/ END PARTIAL WORK PROGRESS/)[1];const context={window:{}};vm.createContext(context);vm.runInContext(source,context);assert.equal(context.window.workProgress.percent([{subtasks:[{done:true},{done:false}]},{}]),25);
  console.log('UNIT_PROGRESS_VERIFIED: 26%, 0%, 100%, no-task fallback; English/Portuguese; mobile/desktop; PDF; reduced motion and print.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
