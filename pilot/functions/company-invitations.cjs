'use strict';
const {randomBytes, createHash} = require('node:crypto');
const {RegistrationError} = require('./company-registration.cjs');
const fail = (code, message) => { throw new RegistrationError(code, message); };
const verified = auth => {
  if (!auth) fail('unauthenticated', 'Entre na sua conta.');
  if (auth.token.email_verified !== true) fail('failed-precondition', 'Confirme seu e-mail primeiro.');
};
const exact = (data, keys) => {
  if (!data || typeof data !== 'object' || Array.isArray(data) || Object.keys(data).some(key => !keys.includes(key)))
    fail('invalid-argument', 'Dados do convite inválidos.');
};
const inviteRef = (db, token) => {
  if (typeof token !== 'string' || !/^[a-f0-9]{64}$/.test(token)) fail('invalid-argument', 'Convite inválido.');
  return db.doc('companyInvites/' + createHash('sha256').update(token).digest('hex'));
};

async function createCompanyInvite({db,auth,data,timestamp,now = Date.now}) {
  verified(auth); exact(data,['email','role']);
  const email = typeof data.email === 'string' ? data.email.trim().toLowerCase() : '';
  const role = data.role || 'employee';
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !['employee','supervisor'].includes(role))
    fail('invalid-argument', 'Informe um e-mail válido e um perfil de funcionário ou supervisor.');
  const token = randomBytes(32).toString('hex');
  const ref = inviteRef(db,token);
  return db.runTransaction(async tx => {
    const index = await tx.get(db.doc('userCompanies/'+auth.uid));
    if (!index.exists) fail('permission-denied', 'Somente o administrador pode convidar.');
    const companyId = index.data().companyId;
    const member = await tx.get(db.doc(`companies/${companyId}/members/${auth.uid}`));
    const company = await tx.get(db.doc('companies/'+companyId));
    if (!member.exists || member.data().role !== 'owner' || !company.exists)
      fail('permission-denied', 'Somente o administrador pode convidar.');
    const expiresAtMs = now() + 7 * 24 * 60 * 60 * 1000;
    tx.create(ref,{companyId,email,role,createdBy:auth.uid,createdAt:timestamp(),expiresAtMs,status:'pending'});
    return {token,email,role,companyName:company.data().name,expiresAtMs};
  });
}

async function acceptCompanyInvite({db,auth,data,timestamp,now = Date.now}) {
  verified(auth); exact(data,['token','name']);
  const name = typeof data.name === 'string' ? data.name.trim() : '';
  if (name.length < 2 || name.length > 120) fail('invalid-argument', 'Informe seu nome (2–120 caracteres).');
  const ref = inviteRef(db,data.token);
  return db.runTransaction(async tx => {
    const invitation = await tx.get(ref);
    if (!invitation.exists) fail('not-found', 'Convite não encontrado.');
    const invite = invitation.data();
    if (invite.email !== (auth.token.email || '').toLowerCase()) fail('permission-denied', 'Entre com o e-mail que recebeu este convite.');
    const indexRef = db.doc('userCompanies/'+auth.uid);
    const memberRef = db.doc(`companies/${invite.companyId}/members/${auth.uid}`);
    const index = await tx.get(indexRef);
    const member = await tx.get(memberRef);
    const company = await tx.get(db.doc('companies/'+invite.companyId));
    if (!company.exists) fail('not-found', 'Empresa não encontrada.');
    if (invite.status === 'accepted' && invite.acceptedBy === auth.uid && index.exists && index.data().companyId === invite.companyId && member.exists)
      return {companyId:invite.companyId,accepted:false};
    if (invite.status !== 'pending') fail('failed-precondition', 'Este convite já foi utilizado ou revogado.');
    if (invite.expiresAtMs <= now()) fail('deadline-exceeded', 'O convite expirou. Peça um novo ao administrador.');
    if (index.exists || member.exists) fail('failed-precondition', 'Esta conta já está vinculada a uma empresa.');
    if (!['employee','supervisor'].includes(invite.role)) fail('failed-precondition', 'Perfil do convite inválido.');
    // Removing/demoting the inviter invalidates outstanding invitations.
    const inviter = await tx.get(db.doc(`companies/${invite.companyId}/members/${invite.createdBy}`));
    if (!inviter.exists || inviter.data().role !== 'owner') fail('failed-precondition', 'Peça um novo convite ao administrador atual.');
    tx.create(memberRef,{role:invite.role,name,email:invite.email,createdAt:timestamp(),invitedBy:invite.createdBy});
    tx.create(indexRef,{companyId:invite.companyId,role:invite.role,createdAt:timestamp()});
    tx.update(ref,{status:'accepted',acceptedBy:auth.uid,acceptedAt:timestamp()});
    return {companyId:invite.companyId,accepted:true};
  });
}

async function revokeCompanyInvite({db,auth,data,timestamp}) {
  verified(auth); exact(data,['token']);
  const ref = inviteRef(db,data.token);
  return db.runTransaction(async tx => {
    const invite = await tx.get(ref);
    if (!invite.exists) fail('not-found', 'Convite não encontrado.');
    const member = await tx.get(db.doc(`companies/${invite.data().companyId}/members/${auth.uid}`));
    if (!member.exists || member.data().role !== 'owner') fail('permission-denied', 'Somente o administrador pode revogar.');
    if (invite.data().status === 'accepted') fail('failed-precondition', 'Este convite já foi aceito.');
    tx.update(ref,{status:'revoked',revokedAt:timestamp()});
    return {revoked:true};
  });
}
module.exports = {createCompanyInvite,acceptCompanyInvite,revokeCompanyInvite};
