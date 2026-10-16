import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const requireFunctions = createRequire(new URL('./functions/package.json', import.meta.url));
const {initializeApp, deleteApp} = requireFunctions('firebase-admin/app');
const {getFirestore, FieldValue} = requireFunctions('firebase-admin/firestore');
import registration from './functions/company-registration.cjs';
import invitations from './functions/company-invitations.cjs';

// Local operation counts are a baseline, not a billing measurement.
assert.match(process.env.FIRESTORE_EMULATOR_HOST || '', /^(127\.0\.0\.1|localhost):\d+$/,
  'This script may only run against the local Firestore emulator.');
const app = initializeApp({projectId:'demo-obra-company-pilot'}, 'consumption-tests');
const db = getFirestore(app);
const owner = {uid:'cost-owner',token:{email_verified:true,email:'cost-owner@example.invalid'}};
const employee = {uid:'cost-employee',token:{email_verified:true,email:'cost-employee@example.invalid'}};
const measurements = [];
async function measure(operation, handler, auth, data, expected) {
  const counts = {operation,transactionAttempts:0,documentReadRequests:0,documentWriteRequests:0};
  const measuredDb = {
    doc: path => db.doc(path), collection: path => db.collection(path),
    runTransaction: callback => db.runTransaction(async tx => {
      counts.transactionAttempts++;
      return callback({
        get: ref => {counts.documentReadRequests++; return tx.get(ref);},
        create: (ref,value) => {counts.documentWriteRequests++; tx.create(ref,value);},
        update: (ref,value) => {counts.documentWriteRequests++; tx.update(ref,value);}
      });
    })
  };
  const result = await handler({db:measuredDb,auth,data,timestamp:()=>FieldValue.serverTimestamp()});
  assert.deepEqual([counts.documentReadRequests,counts.documentWriteRequests],expected);
  assert.equal(counts.transactionAttempts,1,'Baseline assumes no transaction retry.');
  measurements.push(counts);
  return result;
}
try {
  // A dedicated demo project and synthetic users; fixtures are reset only in the emulator.
  const reset = await fetch(`http://${process.env.FIRESTORE_EMULATOR_HOST}/emulator/v1/projects/demo-obra-company-pilot/databases/(default)/documents`,{method:'DELETE'});
  assert.equal(reset.ok,true);
  const data = {name:'Synthetic Cost Company',ownerName:'Test Owner'};
  await measure('register-company',registration.registerCompany,owner,data,[1,3]);
  await measure('register-company-retry',registration.registerCompany,owner,data,[1,0]);
  const invite = await measure('create-invite',invitations.createCompanyInvite,owner,{email:employee.token.email,role:'employee'},[3,1]);
  await measure('accept-invite',invitations.acceptCompanyInvite,employee,{token:invite.token,name:'Test Employee'},[5,3]);
  await measure('accept-invite-retry',invitations.acceptCompanyInvite,employee,{token:invite.token,name:'Test Employee'},[4,0]);
  const revocable = await measure('create-second-invite',invitations.createCompanyInvite,owner,{email:'other@example.invalid',role:'supervisor'},[3,1]);
  await measure('revoke-invite',invitations.revokeCompanyInvite,owner,{token:revocable.token},[2,1]);
  console.log(JSON.stringify({status:'passed',environment:'local Firestore emulator only',measurements,
    excludes:['client reads','Security Rules dependent reads','Auth and email','compute billing','network bytes','photos','build and artifact storage'],
    warning:'These are application-level requests, not measured cloud charges. Retries and other app traffic add usage.'},null,2));
} finally {await db.terminate(); await deleteApp(app);}
