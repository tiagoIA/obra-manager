const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 const context=vm.createContext({URL,console});const cache=new Map();
 async function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod=new vm.SourceTextModule(fs.readFileSync(file,'utf8'),{context,identifier:file});cache.set(file,mod);await mod.link((name,from)=>load(path.resolve(path.dirname(from.identifier),name.split('?')[0])));return mod;}
 const module=await load('public/shopping-catalog.js');await module.evaluate();const {filterCatalog}=module.namespace;const a=cache.get(path.resolve('public/material-attributes.js')).namespace;
 for(const input of ['½','half inch','0.5 in.','1 / 2','1/2 inch'])assert.equal(a.canonicalSize(input),'1/2 in.',input);
 for(const input of ['1¼','1 1/4','1-1/4 in.','1.25'])assert.equal(a.canonicalSize(input),'1-1/4 in.',input);
 assert.equal(a.familyOf({name:'200 A Main Breaker Load Center',family:'breakers'}),'panels');assert.equal(a.familyOf({name:'Load Center',family:'breakers'}),'panels');assert.equal(a.familyOf({name:'AC Disconnect',family:'breakers'}),'disconnects');assert.equal(a.familyOf({name:'20 A breaker',family:'breakers'}),'breakers');
 assert.equal(a.familyOf({cat:'fire',name:'Fire alarm panel'}),'fire-controls');
 assert.equal(a.protectionOf({name:'20 A breaker'}),'');assert.equal(a.protectionOf({name:'20 A Dual Function AFCI/GFCI Breaker'}),'Dual Function');assert.equal(a.protectionOf({name:'20 A Arc Fault Breaker'}),'AFCI');
 const products=[{id:'a',name:'Breaker 20 A',family:'breakers',cat:'eletrica',brand:'Example',series:'Line A',protection:'AFCI',poles:'1',variantGroup:'Line A',manufacturerPart:'A20',unit:'ea'}, {id:'b',name:'Breaker 30 A',family:'breakers',cat:'eletrica',brand:'Example',series:'Line A',protection:'GFCI',poles:'2',variantGroup:'Line A',manufacturerPart:'A30',unit:'ea'}, {id:'c',name:'Breaker 20 A',family:'breakers',brand:'Other',variantGroup:'Line A',unit:'ea'}];
 const before=JSON.stringify(products);assert.deepEqual(Array.from(filterCatalog(products,{family:'breakers',type:'AFCI',amps:'20 A',poles:'1',series:'Line A'}),m=>m.id),['a']);assert.equal(filterCatalog(products,{type:'Standard'}).length,0);
 assert.equal(a.groupVariants(products).length,2);assert.equal(a.groupVariants(products)[0].variants.length,2);assert.equal(a.groupVariants(products.map(p=>({...p,variantGroup:''}))).length,3);assert.equal(JSON.stringify(products),before);
 assert.equal(a.compatibilityVerified({brand:'Square D',series:'QO'}),false);assert.throws(()=>a.validateAttributes({compatibilityStatus:'verified',compatiblePanels:'QO'}));assert.equal(a.compatibilityVerified({compatibilityStatus:'verified',compatiblePanels:'Example panel',compatibilitySource:'https://manufacturer.example/reference'}),true);
 assert.equal(a.tradeSizes({name:'Box 4 in. square',family:'boxes'}).length,0);assert.equal(a.tradeSizes({name:'Wire 12/2 AWG',family:'wiring'}).length,0);assert.equal(a.tradeSizes({name:'Half inch EMT connector',family:'fittings'})[0],'1/2 in.');
 assert.equal(a.facetKeys('fittings').includes('amps'),false);assert.equal(a.facetKeys('breakers').includes('size'),false);
 assert.equal(filterCatalog([{name:'EMT Connector 1/2 in.',family:'fittings'}],{term:'half inch connector'}).length,1);
 const html=fs.readFileSync('public/app.html','utf8');for(const key of ['catalogFamily','protection','tradeSize','variantGroup','compatibilitySource','poles','series','amperage'])assert.ok(html.slice(html.indexOf('const keys=')).includes("'"+key+"'"),'Live save adapter persists '+key);
 console.log('PASS: exact breaker facets, no inferred Standard/compatibility, legacy split, inch aliases, isolated variant identities and persisted attributes.');
})().catch(e=>{console.error(e);process.exitCode=1;});
