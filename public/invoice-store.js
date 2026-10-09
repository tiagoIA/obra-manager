import {digest,invoiceIdentity} from './purchasing-core.js?v=1';
// One transaction writes the complete receipt. Material stock is never written.
export async function persistPurchase(inv,attachment,host){
 const uid=host.userId();if(!uid)throw Error('Sign in again.');
 const id='purchase-'+await digest(invoiceIdentity(inv));
 if(!host.project(inv.projectId))throw Error('This project is unavailable. Choose it again.');
 let uploaded=null;
 try{
  if(attachment)uploaded=await host.upload(id,attachment);
  await host.transaction(async tx=>{
   const current=await tx.get('invoices',id);
   const project=await tx.get('projects',inv.projectId);
   if(current)throw Error('This invoice or receipt is already saved.');
   if(!project)throw Error('This project was removed. Choose another project.');
   const {items,...header}=inv;
   tx.set('invoices',id,{...header,imgUrl:uploaded?.url||null,attachmentPath:uploaded?.path||null,createdBy:uid,createdAt:host.timestamp(),schemaVersion:2,status:'posted'});
   items.forEach((item,n)=>tx.set('invoiceItems',id+'-'+String(n+1).padStart(3,'0'),{...item,invoiceId:id,createdAt:host.timestamp()}));
  });
  return id;
 }catch(e){if(uploaded)await host.removeUpload(uploaded.path).catch(()=>{});throw e;}
}
