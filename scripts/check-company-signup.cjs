const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const base = 'http://127.0.0.1:5000';
const out = 'company-pilot-results';
fs.mkdirSync(out, {recursive:true});
let checks = 0;
const password = 'Pilot-example-2026!'; // Synthetic emulator accounts only.
const expectVisible = async locator => {
  await locator.waitFor({state:'visible',timeout:25000}); checks++;
};

async function verifiedSignup(browser, company, slug) {
  const context = await browser.newContext({viewport:{width:390,height:844}});
  await prepareContext(context);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base);
  await page.locator('#signup button').waitFor({state:'visible'});
  // Wait for Firebase initialization before using the form.
  await page.waitForFunction(() => document.getElementById('signup').onsubmit !== null);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false); checks++;
  if (slug === 'cfc') await page.screenshot({path:out+'/signup-mobile.png',fullPage:true});
  await page.locator('#signup [name=company]').fill(company);
  await page.locator('#signup [name=owner]').fill(company+' Test Admin');
  await page.locator('#signup [name=email]').fill(slug+'@example.invalid');
  await page.locator('#signup [name=password]').fill(password);
  await page.locator('#signup button').click();
  await page.waitForFunction(() => document.getElementById('status').textContent.includes('Enviamos um link'));
  checks++;
  // Unverified accounts cannot create a company.
  await page.locator('#finish').click();
  await page.waitForFunction(() => document.getElementById('status').textContent.includes('ainda não foi confirmado'));
  checks++;
  const codes = await (await fetch('http://127.0.0.1:9099/emulator/v1/projects/demo-obra-company-pilot/oobCodes')).json();
  const code = codes.oobCodes.find(item => item.email === slug+'@example.invalid' && item.requestType === 'VERIFY_EMAIL');
  assert.ok(code); checks++;
  const verified = await fetch('http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:update?key=demo-key', {
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({oobCode:code.oobCode})
  });
  assert.equal(verified.status,200); checks++;
  await page.locator('#finish').click();
  await expectVisible(page.locator('#workspace'));
  assert.equal(await page.locator('#company-name').textContent(),company); checks++;
  await page.screenshot({path:out+'/'+slug+'-workspace-mobile.png',fullPage:true});
  const identity = await page.evaluate(async () => {
    const {getAuth} = await import('https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js');
    const {getFirestore,getDoc,doc} = await import('https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js');
    const user = getAuth().currentUser;
    const index = await getDoc(doc(getFirestore(),'userCompanies',user.uid));
    return {uid:user.uid,token:await user.getIdToken(),companyId:index.data().companyId};
  });
  assert.deepEqual(errors,[]); checks++;
  return {context,page,identity};
}

async function prepareContext(context) {
  if (process.env.FIREBASE_SDK_CACHE) {
    await context.route('https://www.gstatic.com/firebasejs/10.12.0/*.js',route => {
      const filename = path.basename(new URL(route.request().url()).pathname);
      return route.fulfill({path:path.join(process.env.FIREBASE_SDK_CACHE,filename),contentType:'text/javascript',headers:{'Access-Control-Allow-Origin':'*'}});
    });
  }
}

(async () => {
  const options = {headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})};
  if (process.env.HTTPS_PROXY) {
    const proxy = new URL(process.env.HTTPS_PROXY);
    options.proxy = {server:proxy.protocol+'//'+proxy.host,bypass:'127.0.0.1,localhost',username:decodeURIComponent(proxy.username),password:decodeURIComponent(proxy.password)};
  }
  const browser = await chromium.launch(options);
  try {
    const cfc = await verifiedSignup(browser,'CFC Electric','cfc');
    const pnv = await verifiedSignup(browser,'PNV Electric','pnv');
    assert.notEqual(cfc.identity.companyId,pnv.identity.companyId); checks++;
    for (const [reader,target] of [[cfc,pnv],[pnv,cfc]]) {
      const response = await fetch(`http://127.0.0.1:8180/v1/projects/demo-obra-company-pilot/databases/(default)/documents/companies/${target.identity.companyId}`, {
        headers:{Authorization:'Bearer '+reader.identity.token}
      });
      assert.equal(response.status,403); checks++;
    }
    // Generate a real callable invitation in the CFC owner's browser.
    await cfc.page.locator('#invite-form [name=email]').fill('crew@example.invalid');
    await cfc.page.locator('#invite-form button').click();
    await expectVisible(cfc.page.locator('#invite-result'));
    const inviteUrl = await cfc.page.locator('#invite-link').inputValue();
    assert.match(inviteUrl,/#invite=[a-f0-9]{64}$/);checks++;
    const crewContext = await browser.newContext({viewport:{width:390,height:844}});
    await prepareContext(crewContext);
    const crew = await crewContext.newPage();
    await crew.goto(inviteUrl);
    await crew.waitForFunction(() => document.getElementById('signup').onsubmit !== null);
    assert.equal(await crew.locator('#company-field').isVisible(),false);checks++;
    await crew.locator('#signup [name=owner]').fill('Crew Test User');
    await crew.locator('#signup [name=email]').fill('crew@example.invalid');
    await crew.locator('#signup [name=password]').fill(password);
    await crew.locator('#signup button').click();
    await crew.waitForFunction(() => document.getElementById('status').textContent.includes('Enviamos um link'));
    const codes = await (await fetch('http://127.0.0.1:9099/emulator/v1/projects/demo-obra-company-pilot/oobCodes')).json();
    const code = codes.oobCodes.find(item => item.email === 'crew@example.invalid' && item.requestType === 'VERIFY_EMAIL');
    assert.ok(code);checks++;
    const confirmation = await fetch('http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:update?key=demo-key',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({oobCode:code.oobCode})
    });
    assert.equal(confirmation.status,200);checks++;
    await crew.locator('#finish').click();
    await expectVisible(crew.locator('#workspace'));
    assert.equal(await crew.locator('#company-name').textContent(),'CFC Electric');checks++;
    assert.equal(await crew.locator('#member-role').textContent(),'Funcionário');checks++;
    assert.equal(await crew.locator('#invite-panel').isVisible(),false);checks++;
    assert.equal(new URL(crew.url()).hash,'');checks++;
    await crew.screenshot({path:out+'/invited-member-mobile.png',fullPage:true});
    await crew.goto(inviteUrl);
    await expectVisible(crew.locator('#finish'));
    await crew.locator('#finish').click();
    await crew.waitForFunction(() => location.hash === '');
    assert.equal(await crew.locator('#company-name').textContent(),'CFC Electric');checks++;
    assert.equal(await crew.locator('#member-role').textContent(),'Funcionário');checks++;
    await cfc.page.locator('#logout').click();
    await cfc.page.waitForFunction(() => document.getElementById('company-name').textContent === '' && document.getElementById('workspace').hidden);
    checks++;
    await cfc.page.locator('summary').click();
    await cfc.page.locator('#login [name=email]').fill('pnv@example.invalid');
    await cfc.page.locator('#login [name=password]').fill(password);
    await cfc.page.locator('#login button').click();
    await expectVisible(cfc.page.locator('#workspace'));
    assert.equal(await cfc.page.locator('#company-name').textContent(),'PNV Electric'); checks++;
    const summary = {checks,status:'passed',companies:['CFC Electric','PNV Electric'],invitation:'CFC employee accepted verified email-bound invitation',environment:'local emulators only',productionChanged:false};
    fs.writeFileSync(out+'/browser-result.json',JSON.stringify(summary,null,2));
    console.log('PASS browser signup: '+JSON.stringify(summary));
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
