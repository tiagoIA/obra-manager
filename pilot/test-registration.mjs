import fs from 'node:fs';
import assert from 'node:assert/strict';
import {initializeTestEnvironment, assertFails, assertSucceeds} from '@firebase/rules-unit-testing';
import {doc, getDoc, getDocs, collection, setDoc, updateDoc} from 'firebase/firestore';
import {createRequire} from 'node:module';
const requireFunctions = createRequire(new URL('./functions/package.json', import.meta.url));
const {initializeApp, deleteApp} = requireFunctions('firebase-admin/app');
const {getFirestore, FieldValue} = requireFunctions('firebase-admin/firestore');
import service from './functions/company-registration.cjs';
const projectId = 'demo-obra-company-pilot';
const env = await initializeTestEnvironment({projectId, firestore: {host:'127.0.0.1',port:8180,rules:fs.readFileSync('firestore.rules','utf8')}});
const app = initializeApp({projectId}, 'registration-tests');
const db = getFirestore(app);
let checks = 0;
const run = (uid, data, verified = true) => service.registerCompany({db, auth:uid ? {uid, token:{email_verified:verified,email:uid+'@example.invalid'}} : null, data, timestamp:() => FieldValue.serverTimestamp()});
const reject = async (promise, code) => { await assert.rejects(promise, error => error.code === code); checks++; };
try {
  await env.clearFirestore();
  await reject(run(null,{name:'CFC Electric',ownerName:'Test Admin'}),'unauthenticated');
  await reject(run('cfc-test',{name:'CFC Electric',ownerName:'Test Admin'},false),'failed-precondition');
  await reject(run('cfc-test',{name:' ',ownerName:'Test Admin'}),'invalid-argument');
  await reject(run('cfc-test',{name:'CFC Electric',ownerName:'Test Admin',companyId:'other'}),'invalid-argument');
  await reject(run('cfc-test',{name:'CFC Electric',ownerName:'Test Admin',role:'owner'}),'invalid-argument');
  const [first, retry] = await Promise.all([
    run('cfc-test',{name:'CFC Electric',ownerName:'CFC Test Admin'}),
    run('cfc-test',{name:'CFC Electric',ownerName:'CFC Test Admin'})
  ]);
  assert.equal(first.companyId, retry.companyId); checks++;
  assert.equal([first,retry].filter(result => result.created).length,1); checks++;
  const second = await run('pnv-test',{name:'PNV Electric',ownerName:'PNV Test Admin'});
  assert.notEqual(first.companyId,second.companyId); checks++;
  const cfc = env.authenticatedContext('cfc-test').firestore();
  const other = env.authenticatedContext('pnv-test').firestore();
  const ownIndex = await assertSucceeds(getDoc(doc(cfc,'userCompanies/cfc-test'))); checks++;
  assert.equal(ownIndex.data().companyId,first.companyId); checks++;
  await assertFails(getDoc(doc(other,'userCompanies/cfc-test'))); checks++;
  await assertFails(getDocs(collection(cfc,'userCompanies'))); checks++;
  await assertFails(setDoc(doc(cfc,'userCompanies/cfc-test'),{companyId:second.companyId,role:'owner'})); checks++;
  const company = await assertSucceeds(getDoc(doc(cfc,'companies',first.companyId))); checks++;
  assert.equal(company.data().name,'CFC Electric'); checks++;
  assert.equal((await getDoc(doc(cfc,'companies',first.companyId,'members','cfc-test'))).data().role,'owner'); checks++;
  await assertFails(getDoc(doc(other,'companies',first.companyId))); checks++;
  await assertFails(getDoc(doc(cfc,'companies',second.companyId))); checks++;
  await assertFails(updateDoc(doc(other,'companies',first.companyId),{name:'Intrusion'})); checks++;
  await assertFails(setDoc(doc(other,'companies',first.companyId,'members','pnv-test'),{role:'owner'})); checks++;
  const projects = await assertSucceeds(getDocs(collection(cfc,'companies',first.companyId,'projects'))); checks++;
  assert.equal(projects.size,0); checks++;
  await assertFails(getDocs(collection(other,'companies',first.companyId,'projects'))); checks++;
  console.log(`PASS ${checks} registration checks: CFC Electric and PNV Electric isolated, verified identity required, concurrent retries idempotent, owner provisioned atomically, membership/index tampering blocked. Emulator data only.`);
} finally {await env.cleanup();await db.terminate();await deleteApp(app);}
