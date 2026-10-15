const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 const context=vm.createContext({console,Uint8Array,ArrayBuffer,Date,setTimeout,clearTimeout,Blob,File,URL,DOMException});
 const modules=new Map();async function get(file){file=path.resolve(file);if(modules.has(file))return modules.get(file);const module=new vm.SourceTextModule(fs.readFileSync(file,'utf8'),{context,identifier:file});modules.set(file,module);await module.link((name,from)=>get(path.resolve(path.dirname(from.identifier),name.split('?')[0])));return module;}
 const pdfModule=await get('public/photo-report-pdf.js');await pdfModule.evaluate();const reportModule=await get('public/photo-report.js');await reportModule.evaluate();
 const pdf=pdfModule.namespace,report=reportModule.namespace;
 const local=fs.existsSync('tmp/fixtures/images.json')?JSON.parse(fs.readFileSync('tmp/fixtures/images.json')).map(f=>path.join('tmp/fixtures',f).replace(/\.png$/,'.jpg')):['scripts/fixtures/0.jpg','scripts/fixtures/1.jpg'];
 const loadImage=async url=>new Uint8Array(fs.readFileSync(url));
 const counts=[5,9,7,12,4,8,2,3,4,4,8,35];let seq=0;
 const model={project:{name:'Layout test — 101 photos',address:'Test fixture'},filters:{},totalPhotos:101,done:87,pending:0,units:counts.map((count,n)=>({room:{name:'Test unit '+(n+1),floor:'1st floor'},service:n===11?'condensers':'coax',tasks:Array.from({length:n===11?10:7},(_,i)=>({name:'Recorded task '+i,done:true})),notes:[],photos:Array.from({length:count},(_,i)=>({number:++seq,url:local[(seq-1)%local.length],references:[{source:'note',sourceId:'test-'+seq,description:i===0?'Location map — Test fixture.':'Recorded photo '+seq+' with a deliberately long caption to verify the complete description remains together with its photograph.',date:'2026-10-15',status:'complete',stage:'unspecified'}]}))}))};
 const strings={title:'Photographic work report 2.0',units:'Units / work groups',photos:'Unique photos',done:'Completed tasks',pending:'Pending tasks',complete:'Completed',history:'Historical field records',historical:'Photo dates and field notes document their recorded conditions.',contents:'Contents',filters:'Applied filters',all:'Whole project',coax:'Coaxial cabling',condensers:'Condensers',photo:'Photo',field:'Field records',noPhotos:'No photos recorded for this unit.'};
 const options={strings,captionTitle:report.captionTitle,photoSheets:report.photoSheets,loadImage};
 const summary=await pdf.createPhotoReportPDF(model,options);
 // Delayed photo loads must overlap, remain bounded, and preserve every photo.
 let active=0,peak=0,loads=0;
 const speedModel={...model,units:[{...model.units[0],photos:Array.from({length:9},(_,i)=>({...model.units[0].photos[0],number:i+1,url:'speed-'+i}))}],totalPhotos:9};
 const speed=await pdf.createPhotoReportPDF(speedModel,{...options,loadImage:async()=>{loads++;active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,10));active--;return loadImage(local[0]);}});
 assert.equal(speed.photos,9);assert.equal(loads,9);assert.equal(peak,3);assert.equal(active,0);
 console.log('Photo preparation overlaps requests with a maximum of three active loads.');
 const completeModel={...model,units:[{...model.units[0],notes:[{id:'note',text:'Historical note '.repeat(600),createdAt:'2026-10-15'}]}],totalPhotos:5};
 const complete=await pdf.createPhotoReportPDF(completeModel,{...options,includeHistory:true});
 assert.equal(summary.photos,101);assert.equal(complete.photos,5);
 assert.equal(pdf.pdfFilename('455 Massachusetts Ave, Arlington, MA'),'455 Massachusetts Ave, Arlington, MA.pdf');
 let refused=false;try{await pdf.createPhotoReportPDF({...model,units:[{...model.units[0],photos:model.units[0].photos.slice(0,1)}]},{...options,loadImage:()=>Promise.reject(new Error('Fixture unavailable'))});}catch{refused=true;}assert.equal(refused,true);
 fs.mkdirSync('tmp/pdfs',{recursive:true});for(const [name,result]of [['summary',summary],['complete',complete]])fs.writeFileSync('tmp/pdfs/'+name+'.pdf',result.bytes);
 // Verify ready-state sharing uses the generated PDF File and a fresh button click.
 class Element{constructor(tag){this.tag=tag;this.children=[];this.style={cssText:''};this.attributes={};}append(...children){this.children.push(...children);}prepend(child){this.children.unshift(child);}insertBefore(child,before){this.children.splice(this.children.indexOf(before),0,child);}setAttribute(k,v){this.attributes[k]=v;}focus(){}remove(){}}
 const body=new Element('body');let shared;
 context.document={createElement:tag=>new Element(tag),body};context.AbortController=AbortController;
 context.navigator={canShare:({files})=>files[0].type==='application/pdf',share:payload=>{shared=payload;return Promise.resolve();}};
 await pdf.exportPhotoReportPDF({...model,units:[{...model.units[0],photos:model.units[0].photos.slice(0,1)}],totalPhotos:1},options);
 for(let i=0;i<100;i++){if(body.children[0].children[0].children[0].textContent==='PDF ready')break;await new Promise(r=>setTimeout(r,10));}
 const box=body.children[0].children[0],actions=box.children[2];assert.equal(box.children[0].textContent,'PDF ready');assert.equal(shared,undefined);
 const download=actions.children.find(c=>c.download);assert.equal(download.download,'Layout test — 101 photos.pdf');
 actions.children.find(c=>c.textContent==='Share PDF').onclick();assert.equal(shared.files[0].name,download.download);assert.equal(shared.files[0].type,'application/pdf');
 const bytes=new Uint8Array(await shared.files[0].arrayBuffer());assert.equal(String.fromCharCode(...bytes.slice(0,5)),'%PDF-');
 console.log(JSON.stringify({summary:{pages:summary.pages,photos:summary.photos},complete:{pages:complete.pages,photos:complete.photos},missingImageRefused:refused,nativeShare:'PDF File, correct name, fresh click'}));
})().catch(error=>{console.error(error);process.exitCode=1;});
