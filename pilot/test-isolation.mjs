import fs from 'node:fs';
import assert from 'node:assert/strict';
import {initializeTestEnvironment, assertFails, assertSucceeds} from '@firebase/rules-unit-testing';
import {doc, collection, getDoc, getDocs, setDoc, updateDoc, deleteDoc} from 'firebase/firestore';
import {ref, uploadBytes, getBytes, deleteObject} from 'firebase/storage';
import {companyScope} from '../public/company-scope.js';
const projectId='demo-obra-company-pilot';
const env=await initializeTestEnvironment({projectId,
  firestore:{host:'127.0.0.1',port:8180,rules:fs.readFileSync('firestore.rules','utf8')},
  storage:{host:'127.0.0.1',port:9299,rules:fs.readFileSync('storage.rules','utf8')}
});
let checks=0;
const ok=async p=>{await assertSucceeds(p);checks++};
const denied=async p=>{await assertFails(p);checks++};
try {
 await env.withSecurityRulesDisabled(async ctx=>{
  const db=ctx.firestore();
  for(const [id,name,uid] of [['cfc-electric','CFC Electric','cfc-owner'],['pnv-electric','PNV Electric','pnv-owner']]){
   await setDoc(doc(db,'companies',id),{name});
   await setDoc(doc(db,'companies',id,'members',uid),{role:'owner'});
  }
  await setDoc(doc(db,'companies/cfc-electric/projects/arlington'),{name:'Arlington',companyId:'cfc-electric',fixtureOnly:true});
 });
 const cfc=env.authenticatedContext('cfc-owner'),pnv=env.authenticatedContext('pnv-owner');
 const stranger=env.authenticatedContext('stranger'),anon=env.unauthenticatedContext();
 const cfcDB=cfc.firestore(),pnvDB=pnv.firestore();
 const own='companies/cfc-electric/projects/arlington';
 await ok(getDoc(doc(cfcDB,own)));
 assert.equal((await getDocs(collection(pnvDB,'companies/pnv-electric/projects'))).size,0);checks++;
 await denied(getDoc(doc(pnvDB,own)));
 await denied(getDocs(collection(pnvDB,'companies/cfc-electric/projects')));
 await denied(updateDoc(doc(pnvDB,own),{name:'changed'}));
 await denied(deleteDoc(doc(pnvDB,own)));
 await denied(setDoc(doc(pnvDB,'companies/cfc-electric/projects/intruder'),{companyId:'cfc-electric'}));
 await denied(setDoc(doc(pnvDB,'companies/pnv-electric/projects/wrong'),{companyId:'cfc-electric'}));
 await denied(updateDoc(doc(cfcDB,own),{companyId:'pnv-electric'}));
 await denied(setDoc(doc(stranger.firestore(),'companies/cfc-electric/members/stranger'),{role:'owner'}));
 await denied(updateDoc(doc(cfcDB,'companies/cfc-electric/members/cfc-owner'),{role:'owner',extra:true}));
 await denied(getDoc(doc(anon.firestore(),own)));
 await denied(getDocs(collection(cfcDB,'projects')));
 await ok(setDoc(doc(pnvDB,'companies/pnv-electric/projects/new'),{companyId:'pnv-electric',name:'PNV new project'}));
 await denied(getDoc(doc(cfcDB,'companies/pnv-electric/projects/new')));
 await ok(updateDoc(doc(cfcDB,'companies/cfc-electric'),{phone:'TEST',logoPath:'companies/cfc-electric/logo.png'}));
 await denied(updateDoc(doc(pnvDB,'companies/cfc-electric'),{name:'PNV'}));
 const bytes=new Uint8Array([137,80,78,71]);
 const path='companies/cfc-electric/photos/test.png';
 const metadata={contentType:'image/png',customMetadata:{companyId:'cfc-electric'}};
 await ok(uploadBytes(ref(cfc.storage(),path),bytes,metadata));
 await ok(getBytes(ref(cfc.storage(),path)));
 await denied(getBytes(ref(pnv.storage(),path)));
 await denied(deleteObject(ref(pnv.storage(),path)));
 await denied(uploadBytes(ref(pnv.storage(),path),bytes,metadata));
 await denied(uploadBytes(ref(pnv.storage(),'companies/pnv-electric/photos/wrong.png'),bytes,metadata));
 await denied(uploadBytes(ref(cfc.storage(),'companies/cfc-electric/photos/script.html'),bytes,{contentType:'text/html',customMetadata:{companyId:'cfc-electric'}}));
 await denied(uploadBytes(ref(cfc.storage(),'tasks/legacy.png'),bytes,metadata));
 const cfcScope=companyScope('cfc-electric'),pnvScope=companyScope('pnv-electric');
 assert.notEqual(cfcScope.queueKey('same-user'),pnvScope.queueKey('same-user'));
 assert.throws(()=>cfcScope.file('../pnv-electric/photo.png'));
 assert.throws(()=>cfcScope.record({companyId:'pnv-electric'}));
 checks+=3;
 console.log('PASS '+checks+' checks: own-company CRUD, empty PNV, cross-company read/write/delete/list denial, membership tampering denial, authenticated photo upload/read/delete isolation, separate upload queues. Synthetic Arlington only; production untouched. Bearer download URLs still require a private media delivery layer before real pilot use.');
} finally {await env.cleanup()}
