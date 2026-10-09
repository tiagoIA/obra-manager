import {digest,invoiceIdentity} from './purchasing-core.js?v=3';
// Complete purchase and items are atomic; stock is never written.
export async function persistPurchase(inv,attachment,host){
 const uid=host.userId();if(!uid)throw Error('Sign in again.');
 const id='purchase-'+await digest(invoiceIdentity(inv));
 if(!host.project(inv.projectId))throw Error('This project is unavailable. Choose it again.');
 const inputs=attachment?(Array.isArray(attachment)?attachment:[attachment]):[];
 if(inputs.length>12)throw Error('Use up to 12 receipt files.');
 const uploaded=[];let attempted=false;
 try{
  for(const a of inputs){const result=await host.upload(id,a);uploaded.push({...result,filename:a.filename||'Receipt',mime:a.mime,fileHash:a.fileHash||null});}
  if(host.userId()!==uid)throw Error('Your account changed. Sign in and review this purchase again.');
  attempted=true;
  await host.transaction(async tx=>{
   const current=await tx.get('invoices',id),project=await tx.get('projects',inv.projectId);
   const room=inv.roomId?await tx.get('rooms',inv.roomId):null;
   const linked=[];for(const mid of new Set(inv.items.map(i=>i.materialId).filter(Boolean)))linked.push(await tx.get('materials',mid));
   if(host.userId()!==uid)throw Error('Your account changed. Review this purchase again.');
   if(current)throw Error('This invoice or receipt is already saved.');
   if(!project)throw Error('This project was removed. Choose another project.');
   if(inv.roomId&&(!room||room.projectId!==inv.projectId))throw Error('The unit does not belong to this project.');
   if(linked.some(m=>!m||m.isTask||m.active===false||m.status==='inactive'||m.recordType==='family'||m.catalogReviewStatus==='needs-identification'))throw Error('A linked product changed. Review the material links.');
   const {items,...header}=inv;
   tx.set('invoices',id,{...header,imgUrl:uploaded[0]?.url||null,attachmentPath:uploaded[0]?.path||null,attachments:uploaded,createdBy:uid,createdAt:host.timestamp(),schemaVersion:3,status:'posted'});
   items.forEach((item,n)=>tx.set('invoiceItems',id+'-'+String(n+1).padStart(3,'0'),{...item,invoiceId:id,createdAt:host.timestamp()}));
  });return id;
 }catch(e){
  // A lost commit acknowledgement must not delete a committed receipt.
  let safe=!attempted;
  if(attempted&&host.readInvoice){try{const h=await host.readInvoice(id);safe=!h||uploaded.every(a=>!(h.attachments||[]).some(b=>b.path===a.path)&&h.attachmentPath!==a.path);}catch{safe=false;}}
  if(safe)for(const a of uploaded)await host.removeUpload(a.path).catch(()=>{});
  throw e;
 }
}
export async function changePurchaseStatus(id,status,reason,host){
 const uid=host.userId();if(!uid)throw Error('Sign in again.');
 if(!['void','posted'].includes(status)||!String(reason||'').trim())throw Error('Enter a reason for this change.');
 await host.transaction(async tx=>{const h=await tx.get('invoices',id);if(!h)throw Error('Purchase not found.');if(host.userId()!==uid)throw Error('Your account changed.');if((h.status||'posted')===status)return;
 tx.set('invoices',id,{...h,status,updatedAt:host.timestamp(),statusHistory:[...(h.statusHistory||[]),{status,reason:String(reason).trim(),by:uid,at:new Date().toISOString()}]});});
}
export async function linkPurchaseItem(itemId,materialId,reason,host){
 const uid=host.userId();if(!uid)throw Error('Sign in again.');
 if(!String(reason||'').trim())throw Error('Enter a reason for the product link.');
 await host.transaction(async tx=>{const item=await tx.get('invoiceItems',itemId);if(!item)throw Error('Purchase item not found.');const h=await tx.get('invoices',item.invoiceId),m=materialId?await tx.get('materials',materialId):null;
 if(!h||h.status==='void')throw Error('Only active purchases can be linked.');
 if(materialId&&(!m||m.isTask||m.active===false||m.status==='inactive'||m.recordType==='family'||m.catalogReviewStatus==='needs-identification'))throw Error('Choose a verified active product.');
 if(host.userId()!==uid)throw Error('Your account changed.');
 tx.set('invoiceItems',itemId,{...item,materialId:materialId||null,linkHistory:[...(item.linkHistory||[]),{from:item.materialId||null,to:materialId||null,reason:String(reason).trim(),by:uid,at:new Date().toISOString()}],updatedAt:host.timestamp()});});
}
