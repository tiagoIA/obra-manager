import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../pilot/package.json',import.meta.url));
const {initializeTestEnvironment,assertFails,assertSucceeds}=require('@firebase/rules-unit-testing');
const {doc,setDoc,getDoc,getDocs,collection,updateDoc}=require('firebase/firestore');
const {ref,uploadBytes,getBytes}=require('firebase/storage');
const env=await initializeTestEnvironment({projectId:'demo-company-production',firestore:{host:'127.0.0.1',port:8180,rules:fs.readFileSync('firestore.rules','utf8')},storage:{host:'127.0.0.1',port:9299,rules:fs.readFileSync('storage.rules','utf8')}});
let checks=0;
const yes=async p=>{await assertSucceeds(p);checks++;};
const no=async p=>{await assertFails(p);checks++;};
try{
 await env.clearFirestore();
 await env.withSecurityRulesDisabled(async ctx=>{
  const db=ctx.firestore();
  await setDoc(doc(db,'users/legacy-owner'),{role:'owner'});
  await setDoc(doc(db,'users/legacy-worker'),{role:'worker'});
  await setDoc(doc(db,'users/legacy-supervisor'),{role:'supervisor'});
  for(const [company,uid] of [['alpha','owner-a'],['beta','owner-b']]){
   await setDoc(doc(db,'companies',company),{name:company});
   await setDoc(doc(db,'companies',company,'members',uid),{role:'owner'});
   await setDoc(doc(db,'userCompanies',uid),{companyId:company,role:'owner'});
   await setDoc(doc(db,'companies',company,'projects','project'),{name:company,companyId:company});
  }
 });
 const legacy=env.authenticatedContext('legacy-owner');
 const worker=env.authenticatedContext('legacy-worker');
 const a=env.authenticatedContext('owner-a'),b=env.authenticatedContext('owner-b'),unknown=env.authenticatedContext('pending-signup');
 const globals=['projects','rooms','tasks','materials','productDB','roomNotes','shoppingLists','shoppingItems','invoices','invoiceItems','clockEntries','jobs','userLocations','reminders','users'];
 for(const kind of globals){
  await yes(setDoc(doc(legacy.firestore(),kind,'fixture'),{name:'Legacy fixture'}));
  await yes(getDocs(collection(worker.firestore(),kind)));
  for(const client of [a,b,unknown]){
   await no(getDoc(doc(client.firestore(),kind,'fixture')));
   await no(getDocs(collection(client.firestore(),kind)));
   await no(setDoc(doc(client.firestore(),kind,'forged'),{companyId:'alpha'}));
  }
 }
 await yes(getDoc(doc(a.firestore(),'userCompanies/owner-a')));
 await no(getDoc(doc(b.firestore(),'userCompanies/owner-a')));
 await no(setDoc(doc(a.firestore(),'userCompanies/owner-a'),{companyId:'beta'}));
 await yes(getDocs(collection(a.firestore(),'companies/alpha/projects')));
 await no(getDocs(collection(b.firestore(),'companies/alpha/projects')));
 await no(getDoc(doc(b.firestore(),'companies/alpha/members/owner-a')));
 await no(getDocs(collection(a.firestore(),'companies')));
 await no(setDoc(doc(a.firestore(),'companies/alpha/projects/forged'),{companyId:'alpha'}));
 await yes(setDoc(doc(legacy.firestore(),'users/legacy-owner/estimates/check'),{createdBy:'legacy-owner',revision:1}));
 await no(getDoc(doc(a.firestore(),'users/legacy-owner/estimates/check')));
 await no(getDoc(doc(worker.firestore(),'users/legacy-owner/estimates/check')));
 const bytes=new Uint8Array([137,80,78,71]);
 for(const path of ['tasks/legacy.png','estimateFiles/legacy-owner/capture/photo.png']){
  const metadata={contentType:'image/png'};
  await yes(uploadBytes(ref(legacy.storage(),path),bytes,metadata));
  await yes(getBytes(ref(legacy.storage(),path)));
  for(const client of [a,b,unknown]){
   await no(getBytes(ref(client.storage(),path)));
   await no(uploadBytes(ref(client.storage(),path),bytes,metadata));
  }
 }
 // Even an accidentally created global profile cannot bypass an established tenant binding.
 await env.withSecurityRulesDisabled(ctx=>setDoc(doc(ctx.firestore(),'users/owner-a'),{role:'owner'}));
 await no(getDoc(doc(a.firestore(),'projects/fixture')));
 await no(getBytes(ref(a.storage(),'tasks/legacy.png')));
 console.log('PASS '+checks+' production-boundary checks: legacy app retained; pending signup and both tenant owners denied all legacy collections/media; company queries isolated.');
}finally{await env.cleanup();}
