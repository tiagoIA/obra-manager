'use strict';
const {onCall, HttpsError} = require('firebase-functions/v2/https');
const {initializeApp} = require('firebase-admin/app');
const {getFirestore, FieldValue} = require('firebase-admin/firestore');
const {registerCompany, RegistrationError} = require('./company-registration.cjs');
const {createCompanyInvite,acceptCompanyInvite,revokeCompanyInvite} = require('./company-invitations.cjs');
const {saveCompanyProject} = require('./company-projects.cjs');
initializeApp();

const callable = handler => onCall({region: 'us-central1', maxInstances: 3}, async request => {
  const projectId = process.env.GCLOUD_PROJECT || process.env.GOOGLE_CLOUD_PROJECT || '';
  // Production use explicitly authorized by product owner on 2026-10-17.
  if (!/^(obra-manager-4ecc7|obra-manager-teste|demo-obra-company-pilot|obra-company-staging[-a-z0-9]*)$/.test(projectId))
    throw new HttpsError('failed-precondition', 'Company registration is available only in the staging project.');
  try {
    return await handler({db: getFirestore(), auth: request.auth, data: request.data, timestamp: () => FieldValue.serverTimestamp()});
  } catch (error) {
    if (error instanceof RegistrationError) throw new HttpsError(error.code, error.message);
    console.error('Company operation failed', {code: error.code || 'unknown'});
    throw new HttpsError('internal', 'Could not register the company. Try again.');
  }
});
exports.registerCompany = callable(async context => {
  const projectId = process.env.GCLOUD_PROJECT || process.env.GOOGLE_CLOUD_PROJECT || '';
  if (projectId === 'obra-manager-4ecc7' && context.auth) {
    const profile = await context.db.doc('users/' + context.auth.uid).get();
    if (profile.exists) throw new RegistrationError('failed-precondition', 'This account belongs to the existing workspace. Use the main application.');
  }
  return registerCompany(context);
});
exports.createCompanyInvite = callable(createCompanyInvite);
exports.acceptCompanyInvite = callable(acceptCompanyInvite);
exports.revokeCompanyInvite = callable(revokeCompanyInvite);

exports.saveCompanyProject = callable(saveCompanyProject);
