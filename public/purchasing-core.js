// Shared identities, units and purchase prices. No inventory changes.
export const normalize = v => String(v ?? '').trim().toLowerCase().replace(/[^a-z0-9]/g,'');
export function supplierName(value){
 const n=normalize(value);
 const aliases={'homedepot':'Home Depot','thehomedepot':'Home Depot','granitecity':'Granite City Electric','granitecityelectric':'Granite City Electric','granitecityelectricsupply':'Granite City Electric','esc':'Electric Supply Center','electricsupplycenter':'Electric Supply Center','adiglobal':'ADI Global','adiglobaldistribution':'ADI Global','northeastelectrical':'NorthEast Electrical','electricalwholesalersne':'Electrical Wholesalers NE','lowes':"Lowe’s"};
 return aliases[n] || String(value||'').trim();
}
export function unitName(v){const n=normalize(v);return ({ea:'ea',each:'ea',un:'ea',unit:'ea',ft:'ft',feet:'ft',lf:'ft',bx:'box',box:'box',pk:'pack',pack:'pack',rl:'roll',roll:'roll',barra:'stick',stick:'stick'})[n]||n;}
export function validBarcode(v){const s=String(v||'').trim();if(!/^(\d{12}|\d{13}|\d{14})$/.test(s)||!Number(s))return false;let sum=0;for(let i=s.length-2,w=3;i>=0;i--,w=w===3?1:3)sum+=Number(s[i])*w;return (10-sum%10)%10===Number(s.at(-1));}
export function catalogMatch(item,company,materials){
 const vendor=normalize(supplierName(company)),code=normalize(item.code),part=normalize(item.manufacturerPart),upc=String(item.upc||item.code||'').trim();
 const desc=normalize(item.description);const matches=[];
 for(const m of materials){if(m.isTask||m.active===false||m.status==='inactive'||m.recordType==='family'||m.catalogReviewStatus==='needs-identification')continue;
 let score=0,reason='';
 if(validBarcode(upc)&&validBarcode(m.upc)&&upc.replace(/^0+/,'')===String(m.upc).replace(/^0+/,'')){score=100;reason='UPC / barcode';}
 else if(code&&(m.suppliers||[]).some(s=>s.matchVerified!==false&&normalize(supplierName(s.name))===vendor&&[s.code,s.internetId,...(s.aliasCodes||[])].some(c=>normalize(c)===code))){score=100;reason='Supplier code';}
 else if(part&&normalize(m.manufacturerPart)===part&&normalize(m.brand)===normalize(item.brand)&&item.brand){score=95;reason='Manufacturer and model';}
 else if(desc&&[m.name,...(m.aliases||[])].some(n=>normalize(n)===desc)){score=70;reason='Exact description — confirm model';}
 if(score)matches.push({id:m.id,score,reason});
 }
 matches.sort((a,b)=>b.score-a.score);const best=matches[0];return {matches,materialId:best&&best.score>=95&&matches.filter(m=>m.score===best.score).length===1?best.id:null};
}
export const money = n => '$'+Number(n||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
export const cents = n => Math.round(Number(n)*100);
function number(v,label){if(v===null||v===undefined||v==='')throw Error('Enter '+label+'.');const n=Number(v);if(!Number.isFinite(n))throw Error('Invalid '+label+'.');return n;}
export function normalizeInvoice(raw){
 const company=supplierName(raw.company);if(!company||normalize(company)==='unknown')throw Error('Enter the supplier name.');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(raw.date||'')||Number.isNaN(Date.parse(raw.date+'T12:00:00Z'))||new Date(raw.date+'T12:00:00Z').toISOString().slice(0,10)!==raw.date)throw Error('Enter the invoice date.');
 if(!raw.projectId)throw Error('Select the project for this purchase.');
 if(!Array.isArray(raw.items)||!raw.items.length||raw.items.length>80)throw Error('Use 1 to 80 items per invoice.');
 const items=raw.items.map((i,n)=>{const label='item '+(n+1),description=String(i.description||'').trim();if(!description)throw Error('Enter the description for '+label+'.');const qty=number(i.qty,'quantity for '+label),unitPrice=number(i.unit_price,'unit price for '+label),totalPrice=number(i.total_price,'total for '+label);if(qty===0||unitPrice<0)throw Error('Check quantity and unit price for '+label+'.');if(Math.abs(cents(qty*unitPrice)-cents(totalPrice))>Math.max(2,Math.ceil(Math.abs(qty)/2)))throw Error('Quantity × price does not match the total for '+label+'. Enter the net unit price after discounts.');return {code:String(i.code||'').trim()||null,description,qty,unit:String(i.unit||'EA').trim(),unitPrice,totalPrice,materialId:i.materialId||null,upc:i.upc||null,manufacturerPart:i.manufacturerPart||null,brand:i.brand||null};});
 const itemsTotal=items.reduce((s,i)=>s+cents(i.totalPrice),0)/100;
 const subtotal=raw.subtotal===null||raw.subtotal===undefined||raw.subtotal===''?itemsTotal:number(raw.subtotal,'subtotal');const tax=number(raw.tax??0,'tax'),shipping=number(raw.shipping??0,'shipping'),adjustment=number(raw.adjustment??0,'other charges / discounts');
 const expected=(cents(subtotal)+cents(tax)+cents(shipping)+cents(adjustment))/100;
 const total=raw.total===null||raw.total===undefined||raw.total===''?expected:number(raw.total,'invoice total');
 if(Math.abs(cents(subtotal)-cents(itemsTotal))>2)throw Error('The subtotal must match the sum of the item totals.');
 if(Math.abs(cents(total)-cents(expected))>2)throw Error('Subtotal, tax, shipping and adjustments do not match the invoice total.');
 return {company,date:raw.date,invoiceNumber:String(raw.invoice_number||'').trim()||null,projectId:raw.projectId,subtotal,tax,shipping,adjustment,total,items,vendorAddress:raw.vendor_address||null,taxId:raw.tax_id||raw.cnpj||null,notes:raw.notes||'',fileHash:raw.fileHash||null};
}
export async function digest(value){const data=typeof value==='string'?new TextEncoder().encode(value):value;const hash=await crypto.subtle.digest('SHA-256',data);return [...new Uint8Array(hash)].map(v=>v.toString(16).padStart(2,'0')).join('');}
export function invoiceIdentity(inv){return inv.invoiceNumber?'vendor:'+normalize(inv.company)+'|number:'+normalize(inv.invoiceNumber):inv.fileHash?'file:'+inv.fileHash:JSON.stringify([normalize(inv.company),inv.date,inv.total,inv.items.map(i=>[normalize(i.code||i.description),i.qty,unitName(i.unit),i.unitPrice,i.totalPrice])]);}
export function existingInvoice(inv,invoices){return invoices.find(old=>old.status!=='void'&&((inv.fileHash&&old.fileHash===inv.fileHash)||(inv.invoiceNumber&&normalize(old.company)===normalize(inv.company)&&normalize(old.invoiceNumber)===normalize(inv.invoiceNumber))));}
export function purchaseHistory(materialId,invoices,items){const headers=new Map(invoices.filter(h=>h.status!=='void').map(h=>[h.id,h]));return items.filter(i=>i.materialId===materialId&&i.qty>0&&i.unitPrice>0&&headers.has(i.invoiceId)).map(i=>{const h=headers.get(i.invoiceId);return {invoiceId:h.id,itemId:i.id,supplier:supplierName(h.company),code:i.code||'',date:h.date||'',price:i.unitPrice,unit:i.unit,source:'invoice',recordedAt:h.createdAt?.seconds||0};}).sort((a,b)=>b.date.localeCompare(a.date)||b.recordedAt-a.recordedAt||b.itemId.localeCompare(a.itemId));}
export function applyPurchasePrices(materials,invoices,items){return materials.map(m=>{const history=purchaseHistory(m.id,invoices,items);if(!history.length)return m;const suppliers=(m.suppliers||[]).map(s=>({...s}));const seen=new Set();for(const h of history){const key=normalize(h.supplier)+'|'+unitName(h.unit);if(seen.has(key))continue;seen.add(key);let s=suppliers.find(s=>normalize(supplierName(s.name))===normalize(h.supplier)&&unitName(s.unit||m.unit)===unitName(h.unit));if(s&&s.priceDate&&s.priceDate>h.date)continue;if(!s){s={name:h.supplier,unit:h.unit};suppliers.push(s);}Object.assign(s,{price:h.price,priceDate:h.date,priceSource:'invoice',invoiceId:h.invoiceId,code:s.code||h.code});}return {...m,suppliers,purchaseHistory:history};});}
export function estimateRow(item,material,supplier=''){
 if(!Number.isFinite(Number(item.qty))||Number(item.qty)<=0)return {price:null,total:null,reason:'Enter quantity'};
 if(!material||material.active===false||material.status==='inactive'||material.recordType==='family'||material.catalogReviewStatus==='needs-identification')return {price:null,total:null,reason:'Confirm exact product'};
 const refs=(material.suppliers||[]).filter(s=>(!supplier||normalize(supplierName(s.name))===normalize(supplierName(supplier)))&&s.price!==''&&s.price!=null&&Number.isFinite(Number(s.price))&&Number(s.price)>0&&s.priceDate);
 const usable=refs.filter(s=>unitName(s.unit||material.unit)===unitName(item.unit));
 if(!usable.length)return {price:null,total:null,reason:refs.length?'Purchase units differ — confirm pack conversion':'No dated price'};
 // A named supplier is required when more than one supplier has prices.
 if(!supplier&&new Set(usable.map(s=>normalize(supplierName(s.name)))).size>1)return {price:null,total:null,reason:'Choose a supplier'};
 usable.sort((a,b)=>String(b.priceDate).localeCompare(String(a.priceDate)));const s=usable[0];return {price:Number(s.price),total:cents(Number(item.qty)*Number(s.price))/100,date:s.priceDate,supplier:s.name,source:s.priceSource||'reference',reason:''};
}
export function estimateList(items,materials,supplier=''){const rows=items.map(i=>({...i,estimate:estimateRow(i,materials.find(m=>m.id===i.matId),supplier)}));return {rows,subtotal:rows.reduce((sum,r)=>sum+cents(r.estimate.total||0),0)/100,missing:rows.filter(r=>r.estimate.total===null).length};}
