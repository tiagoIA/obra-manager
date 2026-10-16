// Use the application's own identity, taxonomy, and validation rules.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {familyOf} from '../public/material-attributes.js';
import {productKeys,validateProduct} from '../public/central-catalog-v1.js';

const [root,output]=process.argv.slice(2);
if(!root||!output)throw Error('Supply discovery root and output JSON.');
const audit=JSON.parse(fs.readFileSync(path.join(root,'catalog-audit.json')));
const seenSource=new Map();
for(const folder of ['homedepot-batch','homedepot-expanded','homedepot-midpages']){
 const location=path.join(root,folder);if(!fs.existsSync(location))continue;
 for(const file of fs.readdirSync(location).filter(f=>f.endsWith('.json')&&f!=='candidates.json')){
  const data=JSON.parse(fs.readFileSync(path.join(location,file)));
  for(const row of data.candidates||[])if(!seenSource.has(row.internetId))seenSource.set(row.internetId,row);
 }
}
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const existingKeys=new Set(audit.materials.flatMap(productKeys));
const existingRefs=new Set(audit.materials.flatMap(m=>(m.suppliers||[]).filter(s=>s.name==='Home Depot').flatMap(s=>[s.internetId,s.code,...(s.aliasCodes||[])].filter(Boolean).map(String))));
const grouped=new Map();const rejected=[];
for(const c of seenSource.values()){
 const key=productKeys(c).find(k=>k.startsWith('mpn:'));
 if(!key||['unbranded','unknown','generic','multiple'].includes(norm(c.brand))){rejected.push({id:c.candidateId,reason:'No verified manufacturer identity'});continue;}
 if(!grouped.has(key))grouped.set(key,[]);grouped.get(key).push(c);
}
const materials=[];
for(const [identity,rows] of grouped){
 if(existingKeys.has(identity)||rows.some(c=>existingRefs.has(String(c.internetId))||(c.storeCode&&existingRefs.has(String(c.storeCode))))){rejected.push({id:rows[0].candidateId,reason:'Existing product or supplier identity'});continue;}
 const presentations=new Set(rows.map(c=>JSON.stringify([c.unit,c.packQuantity||null,c.packUnit||null])));
 if(presentations.size>1){rejected.push({id:rows[0].candidateId,reason:'Same manufacturer model has conflicting purchase presentations'});continue;}
 const c=rows[0];
 if(!c.name||!c.description||!c.photoUrl||!['ea','pack','box','roll','ft','stick','pair','set','case'].includes(c.unit)){
  rejected.push({id:c.candidateId,reason:'Missing name, description, photo or supported source purchase unit'});continue;
 }
 const id='catalog-'+crypto.createHash('sha256').update(identity).digest('hex').slice(0,24);
 let family=familyOf({name:c.name});
 // Color names such as "light almond" must not turn a receptacle into lighting.
 if(family==='lighting'&&/receptacle|outlet|dimmer|wall.?plate|faceplate|light switch/i.test(c.name))family='devices';
 if(['conduit','cable','other'].includes(family)&&/\b(?:strap|clamp|hanger|staple)s?\b/i.test(c.name))family='supports';
 if(family==='other'&&c.catalogFamily)family=c.catalogFamily;
 const attrs={};for(const k of ['tradeSize','length','amperage','wireGauge','cableConfiguration'])if(c[k])attrs[k]=c[k];
 // Attributes only survive in families where they make sense.
 if(!['conduit','fittings','supports'].includes(family))delete attrs.tradeSize;
 if(family!=='cable'){delete attrs.wireGauge;delete attrs.cableConfiguration;}
 if(!['breakers','panels','disconnects','devices','ev'].includes(family))delete attrs.amperage;
 const photos=[...new Set([c.photoUrl,...(c.photoReferences||[]).map(p=>p.url)].filter(Boolean))].slice(0,2);
 const material={id,identity,name:c.name,brand:c.brand,manufacturerPart:c.manufacturerPart,
  cat:'eletrica',catalogFamily:family,family,unit:c.unit,recordType:'product',
  description:c.description,sourceUrl:c.url,photoUrl:photos[0],photoUrls:photos,
  photoReferenceNote:'Supplier product image. Confirm appearance and packaging against the exact model.',
  compatibilityStatus:'unverified',active:true,status:'active',isTask:false,qty:0,
  sku:'CAT-HD-'+c.internetId,...attrs,
  ...(c.packQuantity?{packQuantity:c.packQuantity,packUnit:c.packUnit}:{}),
  suppliers:rows.map(r=>({name:'Home Depot',code:r.storeCode||'',internetId:r.internetId,url:r.url,
   unit:r.unit,matchVerified:true,currency:'USD',price:'',priceDate:'',priceSource:'reference'})),
  catalogSource:'Public retailer product record',catalogSourceDate:c.date,
  catalogSourceItemId:c.internetId,catalogImportBatch:'electrical-2026-10-16',
  catalogReviewStatus:'source-identified',
 };
 try{validateProduct(material,[]);materials.push(material);}catch(error){rejected.push({id:c.candidateId,reason:error.message});}
}
// Every new material also needs to remain unique under the native validator.
const keys=new Set();for(const m of materials)for(const key of productKeys(m)){if(keys.has(key))throw Error('Duplicate prepared identity: '+key);keys.add(key);}
const summary={sourceRecords:seenSource.size,preparedProducts:materials.length,rejected:rejected.length,
 existingActive:audit.activeRecords,existingNamedProducts:audit.activeSpecificProducts,
 families:Object.fromEntries([...new Set(materials.map(m=>m.catalogFamily))].map(f=>[f,materials.filter(m=>m.catalogFamily===f).length])),
 withTwoPhotos:materials.filter(m=>m.photoUrls.length>1).length,liveWrites:0};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify({summary,materials,rejected},null,2));console.log(JSON.stringify(summary));
