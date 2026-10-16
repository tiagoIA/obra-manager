'use strict';
const {onCall, HttpsError} = require('firebase-functions/v2/https');
const {initializeApp} = require('firebase-admin/app');
const {getFirestore, FieldValue} = require('firebase-admin/firestore');
const {registerCompany, RegistrationError} = require('./company-registration.cjs');
const {createCompanyInvite,acceptCompanyInvite,revokeCompanyInvite} = require('./company-invitations.cjs');
initializeApp();

const callable = handler => onCall({region: 'us-central1', maxInstances: 3}, async request => {
  const projectId = process.env.GCLOUD_PROJECT || process.env.GOOGLE_CLOUD_PROJECT || '';
  // This pilot must never provision companies in the current production project.
  if (!/^(demo-obra-company-pilot|obra-company-staging[-a-z0-9]*)$/.test(projectId))
    throw new HttpsError('failed-precondition', 'Company registration is available only in the staging project.');
  try {
    return await handler({db: getFirestore(), auth: request.auth, data: request.data, timestamp: () => FieldValue.serverTimestamp()});
  } catch (error) {
    if (error instanceof RegistrationError) throw new HttpsError(error.code, error.message);
    console.error('Company operation failed', {code: error.code || 'unknown'});
    throw new HttpsError('internal', 'Could not register the company. Try again.');
  }
});
exports.registerCompany = callable(registerCompany);
exports.createCompanyInvite = callable(createCompanyInvite);
exports.acceptCompanyInvite = callable(acceptCompanyInvite);
exports.revokeCompanyInvite = callable(revokeCompanyInvite);
