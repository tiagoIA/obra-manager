export function photoRole(photo){
 const refs=photo.references||[];
 const explicit=refs.find(r=>['facade','map'].includes(r.reportRole))?.reportRole;if(explicit)return explicit;
 if(refs.some(r=>/^storefront\b|^fachada\b/i.test(r.description||'')))return 'facade';
 if(refs.some(r=>/^location map\b|^mapa de localiza/i.test(r.description||'')||/\b(?:floor[ -]?plan|location[ -]?map)\b/i.test(r.name||'')))return 'map';
 return 'work';
}
export function orderPhotos(photos,stageRank){return photos.map((photo,i)=>({photo,i})).sort((a,b)=>{const rank=p=>({facade:0,map:1}[photoRole(p)]??(10+stageRank(p)));return rank(a.photo)-rank(b.photo)||a.i-b.i;}).map(v=>v.photo);}
// Balanced groups avoid 4 + 1 and preserve whole-unit identity before work photos.
export function reportSheets(photos,summary=false){const max=summary?4:2,sheets=[];let batch=[];
 const flush=()=>{let left=batch.length,groups=Math.ceil(left/max),offset=0;for(let g=0;g<groups;g++){const n=Math.ceil(left/(groups-g));sheets.push(batch.slice(offset,offset+n));offset+=n;left-=n;}batch=[];};
 for(const photo of photos){if(photo.layout==='full'){flush();sheets.push([{...photo,fullPage:true}]);}else batch.push({...photo});}flush();return sheets;
}
