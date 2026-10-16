import {initializeApp} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
import {getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, sendEmailVerification, signOut, onAuthStateChanged} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';
import {getFirestore, getDoc, doc} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';
import {getFunctions, httpsCallable} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-functions.js';
const $ = id => document.getElementById(id);
const status = message => { $('status').textContent = message; };
let auth, db, register;
let draft = {name: '', ownerName: ''};
let epoch = 0;
const names = () => {
  const form = $('signup').elements;
  draft = {name: form.company.value.trim(), ownerName: form.owner.value.trim()};
  if (draft.name.length < 2 || draft.ownerName.length < 2) throw Error('Preencha o nome da empresa e seu nome.');
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
  $('workspace').hidden = true;
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
    $('workspace').hidden = false;
    $('cadastro').hidden = true;
    status('');
  } else if (!user.emailVerified) {
    $('verify').hidden = false;
    status('Confirme seu e-mail antes de criar a empresa.');
  } else {
    $('verify').hidden = false;
    status('Preencha o nome da empresa e seu nome acima. Depois conclua o cadastro.');
  }
}
try {
  const response = await fetch('/__/firebase/init.json');
  if (!response.ok) throw Error('Este cadastro precisa ser publicado no ambiente de teste.');
  const config = await response.json();
  if (!/^obra-company-staging[-a-z0-9]*$/.test(config.projectId || '')) throw Error('Cadastro disponível somente no ambiente de teste separado.');
  const app = initializeApp(config);
  auth = getAuth(app); db = getFirestore(app);
  register = httpsCallable(getFunctions(app, 'us-central1'), 'registerCompany');
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
    const existing = await getDoc(doc(db, 'userCompanies', user.uid));
    if (!existing.exists()) await register(names());
    await showUser(user);
  });
  $('resend').onclick = () => busy(async () => {
    if (!auth.currentUser) throw Error('Entre na sua conta primeiro.');
    await sendEmailVerification(auth.currentUser);
    status('Enviamos outro link de confirmação.');
  });
  $('logout').onclick = () => busy(async () => {
    ++epoch;
    await signOut(auth);
    draft = {name: '', ownerName: ''};
    $('signup').reset(); $('login').reset();
    status('Você saiu da conta.');
  });
} catch (error) {
  document.querySelectorAll('button, input').forEach(control => { control.disabled = true; });
  status(error.message);
}
