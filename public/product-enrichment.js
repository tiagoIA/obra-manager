import {supplierName,unitName} from './purchasing-core.js?v=library-1';
const clean=v=>String(v||'').trim().toLowerCase().replace(/[^a-z0-9]/g,'');
export function httpsUrl(value){try{const u=new URL(value);return u.protocol==='https:'?u.href:'';}catch{return '';}}
export function reviewCandidate(material,candidate){
 if(!material||candidate.materialId!==material.id)throw Error('The product ID does not match.');
 if(!httpsUrl(candidate.url)||!candidate.supplier)throw Error('A supplier and HTTPS product source are required.');
 const ref=(material.suppliers||[]).find(r=>supplierName(r.name)===supplierName(candidate.supplier)&&[r.code,r.internetId,...(r.aliasCodes||[])].some(code=>code&&clean(code)===clean(candidate.storeCode)));
 const part=material.manufacturerPart||material.model;
 if(part&&candidate.manufacturerPart&&clean(part)!==clean(candidate.manufacturerPart))throw Error('Manufacturer model conflicts with the saved product.');
 if(material.brand&&candidate.brand&&clean(material.brand)!==clean(candidate.brand))throw Error('Manufacturer conflicts with the saved product.');
 const byModel=!!part&&!!material.brand&&clean(candidate.manufacturerPart)===clean(part)&&clean(candidate.brand)===clean(material.brand);
 if(!ref&&!byModel)throw Error('Confirm a registered store code or exact manufacturer and model first.');
 if(candidate.price!==null&&candidate.price!==undefined&&(!Number.isFinite(Number(candidate.price))||Number(candidate.price)<0||!/^\d{4}-\d{2}-\d{2}$/.test(candidate.date||'')||candidate.currency!=='USD'))throw Error('Use a dated USD price.');
 if(candidate.photoUrl&&!httpsUrl(candidate.photoUrl))throw Error('Use an HTTPS product image.');
 if(candidate.date&&(Number.isNaN(Date.parse(candidate.date+'T12:00:00Z'))||new Date(candidate.date+'T12:00:00Z').toISOString().slice(0,10)!==candidate.date))throw Error('Invalid collection date.');
 return {ref,byModel};
}
export function candidatePatch(material,candidate,unit,photo=false){const {ref}=reviewCandidate(material,candidate);if(!unitName(unit))throw Error('Confirm the supplier purchase unit.');return {supplier:{...(ref||{}),name:supplierName(candidate.supplier),code:ref?.code||candidate.storeCode||'',url:httpsUrl(candidate.url),unit,price:candidate.price==null?(ref?.price??''):Number(candidate.price),priceDate:candidate.price==null?(ref?.priceDate||''):candidate.date,priceSource:candidate.price==null?(ref?.priceSource||'reference'):'online',currency:'USD',location:candidate.location||'',matchVerified:true,lastReviewedAt:new Date().toISOString()},...(photo&&candidate.photoUrl?{photoUrl:httpsUrl(candidate.photoUrl),photoReferenceNote:'Reviewed supplier image · '+candidate.supplier+' · '+candidate.date}:{})};}
