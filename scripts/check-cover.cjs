const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 const context=vm.createContext({console,Uint8Array,ArrayBuffer,Date,setTimeout,clearTimeout,URL,DOMException});const cache=new Map();
 async function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const m=new vm.SourceTextModule(fs.readFileSync(file,'utf8'),{context,identifier:file});cache.set(file,m);await m.link((n,f)=>load(path.resolve(path.dirname(f.identifier),n.split('?')[0])));return m;}
 const mod=await load('public/photo-report-pdf.js');await mod.evaluate();const r=await load('public/photo-report.js');await r.evaluate();const {createPhotoReportPDF}=mod.namespace,{renderPhotoReport,buildPhotoModel,captionTitle,photoSheets}=r.namespace;
 const strings={title:'Photographic work report 2.0',contents:'Contents',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',complete:'Completed',historical:'Photo dates and field notes document recorded conditions.',filters:'Applied filters',all:'Whole project',general:'Units',photo:'Photo',noPhotos:'No photos recorded',none:'No matching photos'};
 const base={project:{name:'3 Bartlett Street',address:'Melrose, MA'},filters:{},units:[{room:{name:'Basement'},service:'general',tasks:[{name:'Install lighting circuit',done:true}],notes:[],photos:[{number:1,url:'https://fixture.test/work.jpg',references:[{source:'task',sourceTitle:'Install lighting circuit',status:'complete'}]}]}],totalPhotos:1,done:1,pending:0};
 fs.mkdirSync('tmp/pdfs',{recursive:true});
 for(const kind of ['landscape','portrait','no-facade','long-title','portuguese']){
  const model=structuredClone(base);if(kind!=='no-facade')model.project.facadePhoto={url:'https://fixture.test/facade.jpg'};if(kind==='long-title')model.project.name='Residential electrical improvements and EV charger installation - Building A, 3 Bartlett Street, Melrose, Massachusetts - Basement lighting, receptacles and boiler circuit';
  let calls=0;const result=await createPhotoReportPDF(model,{strings,captionTitle,photoSheets,language:kind==='portuguese'?'pt':'en',loadImage:async url=>{calls++;return new Uint8Array(fs.readFileSync('scripts/fixtures/'+(url.includes('facade')&&kind==='portrait'?1:0)+'.jpg'));}});
  assert.equal(result.photos,1);assert.equal(result.pages,3);assert.equal(calls,kind==='no-facade'?1:2);fs.writeFileSync('tmp/pdfs/cover-'+kind+'.pdf',result.bytes);
  const html=renderPhotoReport(model);assert.equal((html.match(/class="pr-cover-photo"/g)||[]).length,kind==='no-facade'?0:1);assert.ok(html.indexOf('class="pr-overview"')>html.indexOf('</header>'));assert.equal((html.match(/<strong>Photo 1 /g)||[]).length,1);
 }
 const source={project:{...base.project,facadePhoto:{url:'https://fixture.test/facade.jpg'}},rooms:[{id:'r',name:'Basement'}],tasks:[{id:'t',name:'Test',roomId:'r',photoUrl:'https://fixture.test/work.jpg'}],notes:[]};const before=JSON.stringify(source);assert.equal(buildPhotoModel(source).totalPhotos,1);assert.equal(JSON.stringify(source),before);
 await assert.rejects(createPhotoReportPDF({...base,project:{...base.project,facadePhoto:{url:'https://fixture.test/missing.jpg'}}},{strings,captionTitle,photoSheets,loadImage:async()=>{throw Error('Unavailable')}}),/facade/);
 assert.ok(!renderPhotoReport({...base,project:{name:'<script>bad</script>',facadePhoto:{url:'javascript:alert(1)'}}}).includes('<script>'));
 console.log('PASS: landscape/portrait facade covers, long names, no-facade fallback, Portuguese, independent evidence counts, separate index and failed-facade refusal.');
})().catch(e=>{console.error(e);process.exitCode=1;});
