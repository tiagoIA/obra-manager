'use strict';

class RegistrationError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

// Auth identity comes exclusively from the callable's verified token.
async function registerCompany({db, auth, data, timestamp}) {
  if (!auth) throw new RegistrationError('unauthenticated', 'Sign in to register your company.');
  if (auth.token.email_verified !== true) throw new RegistrationError('failed-precondition', 'Verify your email before registering.');
  const name = typeof data?.name === 'string' ? data.name.trim() : '';
  const ownerName = typeof data?.ownerName === 'string' ? data.ownerName.trim() : '';
  if (name.length < 2 || name.length > 120 || ownerName.length < 2 || ownerName.length > 120)
    throw new RegistrationError('invalid-argument', 'Company and administrator names must contain 2–120 characters.');
  if (Object.keys(data).some(key => !['name', 'ownerName'].includes(key)))
    throw new RegistrationError('invalid-argument', 'Only company and administrator names are accepted.');
  const index = db.doc(`userCompanies/${auth.uid}`);
  const company = db.collection('companies').doc();
  return db.runTransaction(async tx => {
    const existing = await tx.get(index);
    // A repeated submit or network retry returns the original company.
    if (existing.exists) return {companyId: existing.data().companyId, created: false};
    const companyId = company.id;
    tx.create(company, {name, createdAt: timestamp(), createdBy: auth.uid});
    tx.create(company.collection('members').doc(auth.uid), {
      role: 'owner', name: ownerName, email: auth.token.email || '', createdAt: timestamp()
    });
    tx.create(index, {companyId, role: 'owner', createdAt: timestamp()});
    return {companyId, created: true};
  });
}

module.exports = {registerCompany, RegistrationError};
