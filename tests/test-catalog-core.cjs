const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
 const context=vm.createContext({console,URL,TextEncoder,Uint8Array,crypto:globalThis.crypto});const cache=new Map();
 async function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const m=new vm.SourceTextModule(fs.readFileSync(file,'utf8'),{context,identifier:file});cache.set(file,m);await m.link((name,from)=>load(path.resolve(path.dirname(from.identifier),name.split('?')[0])));return m;}
 const module=await load('public/shopping-catalog.js');await module.evaluate();const {filterCatalog,familyOf,tradeSizes,ampRatings}=module.namespace;
 const products=[{id:'a',name:'EMT Connector 3/4 in.',cat:'eletrica',family:'fittings',brand:'Brand A',unit:'ea',manufacturerPart:'C34',suppliers:[{name:'Home Depot',code:'100',price:3,priceDate:'2026-10-15',unit:'ea'}]}, {id:'b',name:'EMT Connector 1/2 in.',cat:'eletrica',brand:'Brand B',unit:'ea',suppliers:[{name:'Home Depot',price:1,priceDate:'2026-10-15',unit:'ea'}]}, {id:'c',name:'40A Breaker',cat:'eletrica',family:'breakers',brand:'Brand A',unit:'ea'}, {id:'d',name:'Smoke Detector',cat:'fire',family:'detectors',unit:'ea'}, {id:'inactive',name:'Inactive connector',cat:'eletrica',active:false}, {id:'task',name:'Install connector',isTask:true}];
 const before=JSON.stringify(products);assert.deepEqual(Array.from(filterCatalog(products,{term:'¾ conector'}),m=>m.id),['a']);
 assert.deepEqual(Array.from(filterCatalog(products,{department:'eletrica',family:'fittings',size:'3/4 in.',brand:'Brand A',supplier:'Home Depot'}),m=>m.id),['a']);
 assert.deepEqual(Array.from(filterCatalog(products,{department:'fire'}),m=>m.id),['d']);
 assert.deepEqual(Array.from(filterCatalog(products,{family:'fittings',sort:'price'}),m=>m.id),['b','a']);
 assert.equal(familyOf(products[2]),'breakers');assert.equal(familyOf(products[3]),'detection');
 assert.deepEqual(Array.from(ampRatings(products[2])),['40 A']);assert.deepEqual(Array.from(tradeSizes({name:'Copper cable 12/2 AWG'})),[]);
 assert.deepEqual(Array.from(filterCatalog(products,{term:'not-in-library'})),[]);
 assert.equal(JSON.stringify(products),before,'Catalog navigation must not change material data');
 console.log('PASS: bilingual fraction search, department/family/brand/size/supplier facets, dated price ordering, recorded ratings, active product filtering and immutable catalog.');
})().catch(error=>{console.error(error);process.exitCode=1;});
