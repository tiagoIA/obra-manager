import {createProjectWorkspace} from './projects.js';
import {initializeApp} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
import {getAuth, connectAuthEmulator, createUserWithEmailAndPassword, signInWithEmailAndPassword, sendEmailVerification, signOut, onAuthStateChanged} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';
import {getFirestore, connectFirestoreEmulator, getDoc, doc} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';
import {getFunctions, connectFunctionsEmulator, httpsCallable} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-functions.js';
const $ = id => document.getElementById(id);
const status = message => { $('status').textContent = message; };
let projects;
let auth, db, register, createInvite, acceptInvite, revokeInvite;
let invitation = new URLSearchParams(location.hash.slice(1)).get('invite');
let generatedToken = null;
let activeRole = null;
function clearInviteResult() {
  generatedToken = null;
  $('invite-link').value = '';
  $('invite-description').textContent = '';
  $('invite-result').hidden = true;
}
function inviteMode() {
  $('company-field').hidden = !!invitation;
  $('signup').elements.company.disabled = !!invitation;
  $('signup-title').textContent = invitation ? 'Entre na sua equipe' : 'Cadastre sua empresa';
  $('verify-help').textContent = invitation ? 'Confirme o e-mail informado pelo administrador. Depois volte aqui para aceitar o convite.' : 'Abra o link enviado ao seu e-mail. Depois volte aqui para concluir o cadastro da empresa.';
  $('finish').textContent = invitation ? 'Confirmar e aceitar convite' : 'Já confirmei meu e-mail';
  $('welcome').hidden = !!invitation;
}
inviteMode();
window.addEventListener('hashchange', () => {
  invitation = new URLSearchParams(location.hash.slice(1)).get('invite');
  inviteMode();
  if (auth) showUser(auth.currentUser).catch(error => status(error.message));
});
let draft = {name: '', ownerName: ''};
let epoch = 0;
const names = () => {
  const form = $('signup').elements;
  draft = {name: form.company.value.trim(), ownerName: form.owner.value.trim()};
  if ((!invitation && draft.name.length < 2) || draft.ownerName.length < 2) throw Error('Preencha os nomes solicitados.');
  return draft;
};
async function busy(action) {
  document.querySelectorAll('button').forEach(button => { button.disabled = true; });
  try { status(''); await action(); }
  catch (error) {
    const messages = {
      'auth/email-already-in-use': 'Este e-mail já possui conta. Use a opção de entrar.',
      'auth/invalid-credential': 'E-mail ou senha incorretos.',
      'auth/too-many-requests': 'Muitas tentativas. Aguarde antes de tentar novamente.',
      'auth/weak-password': 'Use uma senha mais forte, com pelo menos 12 caracteres.',
      'auth/network-request-failed': 'Sem conexão. Tente novamente quando a internet voltar.',
      'functions/unavailable': 'O cadastro está temporariamente indisponível. Tente novamente.'
    };
    status(messages[error.code] || error.message || 'Não foi possível concluir. Tente novamente.');
  } finally { document.querySelectorAll('button').forEach(button => { button.disabled = false; }); }
}
async function showUser(user) {
  const current = ++epoch;
  projects?.clear();
  $('workspace').hidden = true;
  activeRole = null;
  $('member-role').textContent = '';
  $('invite-panel').hidden = true;
  clearInviteResult();
  $('company-name').textContent = '';
  $('verify').hidden = true;
  $('cadastro').hidden = false;
  $('logout').hidden = !user;
  if (!user) return;
  const snap = await getDoc(doc(db, 'userCompanies', user.uid));
  if (current !== epoch || auth.currentUser?.uid !== user.uid) return;
  if (snap.exists()) {
    const company = await getDoc(doc(db, 'companies', snap.data().companyId));
    if (current !== epoch || auth.currentUser?.uid !== user.uid) return;
    if (!company.exists()) throw Error('Empresa não encontrada. Entre em contato com o administrador.');
    $('company-name').textContent = company.data().name;
    activeRole = snap.data().role;
    $('member-role').textContent = {owner:'Administrador',supervisor:'Supervisor',employee:'Funcionário'}[activeRole] || 'Membro';
    $('invite-panel').hidden = activeRole !== 'owner';
    projects.open(snap.data().companyId, activeRole);
    $('workspace').hidden = false;
    $('cadastro').hidden = true;
    if (invitation) {
      $('verify').hidden = false;
      status('Você abriu um convite. Confirme abaixo para verificar o vínculo com sua conta.');
      return;
    }
    status('');
  } else if (!user.emailVerified) {
    $('verify').hidden = false;
    status(invitation ? 'Confirme seu e-mail para aceitar o convite.' : 'Confirme seu e-mail antes de criar a empresa.');
  } else {
    $('verify').hidden = false;
    status(invitation ? 'Informe seu nome acima e aceite o convite.' : 'Preencha o nome da empresa e seu nome acima. Depois conclua o cadastro.');
  }
}
try {
  const local = ['127.0.0.1', 'localhost'].includes(location.hostname);
  let config;
  if (local) {
    config = {projectId:'demo-obra-company-pilot',apiKey:'demo-key',authDomain:'demo-obra-company-pilot.firebaseapp.com',appId:'demo-company-pilot'};
  } else {
    const response = await fetch('/__/firebase/init.json');
    if (!response.ok) throw Error('Este cadastro precisa ser publicado no ambiente de teste.');
    config = await response.json();
    if (!/^(obra-manager-4ecc7|obra-manager-teste|obra-company-staging[-a-z0-9]*)$/.test(config.projectId || '')) throw Error('Cadastro disponível somente no ambiente de teste separado.');
  }
  const app = initializeApp(config);
  auth = getAuth(app); db = getFirestore(app);
  const functions = getFunctions(app, 'us-central1');
  if (local) {
    connectAuthEmulator(auth, 'http://127.0.0.1:9099', {disableWarnings:true});
    connectFirestoreEmulator(db, '127.0.0.1', 8180);
    connectFunctionsEmulator(functions, '127.0.0.1', 5001);
  }
  projects = createProjectWorkspace({db, save: httpsCallable(functions, 'saveCompanyProject'), host: $('projects')});
  register = httpsCallable(functions, 'registerCompany');
  createInvite = httpsCallable(functions, 'createCompanyInvite');
  acceptInvite = httpsCallable(functions, 'acceptCompanyInvite');
  revokeInvite = httpsCallable(functions, 'revokeCompanyInvite');
  onAuthStateChanged(auth, user => { showUser(user).catch(error => status(error.message)); });
  $('signup').onsubmit = event => { event.preventDefault(); busy(async () => {
    names();
    if (auth.currentUser) {
      $('verify').hidden = false;
      return status('Use o botão de confirmação abaixo para concluir com a conta atual.');
    }
    const form = event.target.elements;
    const result = await createUserWithEmailAndPassword(auth, form.email.value.trim(), form.password.value);
    form.password.value = '';
    await sendEmailVerification(result.user);
    status('Enviamos um link de confirmação ao seu e-mail.');
  }); };
  $('login').onsubmit = event => { event.preventDefault(); busy(async () => {
    const form = event.target.elements;
    await signInWithEmailAndPassword(auth, form.email.value.trim(), form.password.value);
    form.password.value = '';
  }); };
  $('finish').onclick = () => busy(async () => {
    const user = auth.currentUser;
    if (!user) throw Error('Entre na sua conta primeiro.');
    await user.reload();
    if (!user.emailVerified) throw Error('Seu e-mail ainda não foi confirmado. Abra o link enviado.');
    await user.getIdToken(true);
    const operationEpoch = epoch;
    if (invitation) {
      let name = $('signup').elements.owner.value.trim() || user.displayName || '';
      if (!name) {
        const currentIndex = await getDoc(doc(db,'userCompanies',user.uid));
        if (currentIndex.exists()) {
          const member = await getDoc(doc(db,'companies',currentIndex.data().companyId,'members',user.uid));
          name = member.data()?.name || '';
        }
      }
      await acceptInvite({token:invitation,name});
      if (operationEpoch !== epoch || auth.currentUser?.uid !== user.uid) return;
      invitation = null;
      history.replaceState(null,'',location.pathname);
      inviteMode();
    } else {
      const existing = await getDoc(doc(db, 'userCompanies', user.uid));
      if (!existing.exists()) await register(names());
    }
    await showUser(user);
  });
  $('invite-form').onsubmit = event => { event.preventDefault(); busy(async () => {
    if (activeRole !== 'owner') throw Error('Somente o administrador pode convidar.');
    clearInviteResult();
    const uid = auth.currentUser?.uid;
    const operationEpoch = epoch;
    const form = event.target.elements;
    const result = await createInvite({email:form.email.value.trim(),role:form.role.value});
    if (operationEpoch !== epoch || auth.currentUser?.uid !== uid) return;
    generatedToken = result.data.token;
    const url = new URL(location.pathname, location.origin);
    url.hash = 'invite='+generatedToken;
    $('invite-link').value = url.href;
    const role = result.data.role === 'supervisor' ? 'Supervisor' : 'Funcionário';
    $('invite-description').textContent = result.data.companyName+' · '+result.data.email+' · '+role+' · válido até '+new Date(result.data.expiresAtMs).toLocaleDateString('pt-BR');
    $('invite-result').hidden = false;
    status('Convite criado. Copie e compartilhe o link com a pessoa convidada.');
  }); };
  $('copy-invite').onclick = () => busy(async () => {
    try { await navigator.clipboard.writeText($('invite-link').value); status('Link copiado.'); }
    catch { $('invite-link').select(); status('Selecione e copie o link acima.'); }
  });
  $('revoke-invite').onclick = () => busy(async () => {
    if (!generatedToken) throw Error('Gere um convite primeiro.');
    await revokeInvite({token:generatedToken});
    clearInviteResult();
    status('Convite revogado.');
  });
  $('resend').onclick = () => busy(async () => {
    if (!auth.currentUser) throw Error('Entre na sua conta primeiro.');
    await sendEmailVerification(auth.currentUser);
    status('Enviamos outro link de confirmação.');
  });
  $('logout').onclick = () => busy(async () => {
    ++epoch;
    projects?.clear();
    activeRole = null;
    clearInviteResult();
    await signOut(auth);
    draft = {name: '', ownerName: ''};
    $('signup').reset(); $('login').reset();
    status('Você saiu da conta.');
  });
  document.querySelectorAll('form').forEach(form => { form.inert = false; });
} catch (error) {
  document.querySelectorAll('button, input').forEach(control => { control.disabled = true; });
  status(error.message);
}
