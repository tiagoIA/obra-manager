'use strict';
const {RegistrationError: E} = require('./company-registration.cjs');
const fail = (code, message) => { throw new E(code, message); };
const id = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{16,80}$/.test(value);
async function saveCompanyProject({db,auth,data,timestamp}) {
  if (!auth) fail('unauthenticated','Sign in first.');
  if (auth.token?.email_verified !== true) fail('failed-precondition','Verify your email.');
  if (!data || Object.keys(data).some(k => !['projectId','revision','name','address','notes','status'].includes(k))) fail('invalid-argument','Invalid project fields.');
  if (!id(data.projectId) || !Number.isInteger(data.revision) || data.revision < 0) fail('invalid-argument','Invalid project version.');
  const fields = {};
  for (const [key,max] of [['name',120],['address',500],['notes',4000]]) {
    if (typeof data[key] !== 'string' || data[key].trim().length > max) fail('invalid-argument','Invalid '+key+'.');
    fields[key] = data[key].trim();
  }
  if (fields.name.length < 2 || !['active','archived'].includes(data.status)) fail('invalid-argument','Enter a project name and valid status.');
  return db.runTransaction(async tx => {
    const index = await tx.get(db.doc('userCompanies/'+auth.uid));
    const companyId = index.data()?.companyId;
    if (!companyId || typeof companyId !== 'string' || companyId.includes('/')) fail('permission-denied','Company membership required.');
    const membership = await tx.get(db.doc(`companies/${companyId}/members/${auth.uid}`));
    if (membership.data()?.role !== 'owner') fail('permission-denied','Only the company owner can manage projects.');
    const ref = db.doc(`companies/${companyId}/projects/${data.projectId}`);
    const existing = await tx.get(ref);
    const old = existing.data();
    const next = {...fields,status:data.status};
    // Retried requests return the saved revision without overwriting newer work.
    if (old && old.companyId === companyId && old.revision === data.revision+1 && Object.entries(next).every(([k,v]) => old[k] === v)) return {projectId:ref.id,revision:old.revision};
    if ((old?.revision || 0) !== data.revision || (old && old.companyId !== companyId)) fail('aborted','This project changed. Reload before saving.');
    if (!old && data.status !== 'active') fail('invalid-argument','New projects must be active.');
    const saved = {...next,companyId,revision:data.revision+1,updatedAt:timestamp(),updatedBy:auth.uid};
    if (!old) Object.assign(saved,{createdAt:timestamp(),createdBy:auth.uid});
    tx.set(ref,saved,{merge:!!old});
    return {projectId:ref.id,revision:saved.revision};
  });
}
module.exports = {saveCompanyProject};
