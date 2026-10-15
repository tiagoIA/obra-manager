const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('public/app.html','utf8');
for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)){if(!m[2].trim())continue;/type=["']module["']/.test(m[1])?new vm.SourceTextModule(m[2]):new vm.Script(m[2]);}
const code=html.slice(html.indexOf('window.renderProjectFacadeThumbnail='),html.indexOf('// Optional service classification'));
let allowed=true,uid='owner',stored={name:'Project A',scope:'electrical',workTypes:['ev-charger']},writes=[],messages=[],compressed=async()=>({type:'image/jpeg'});
const input={dataset:{projectId:'a'},files:[{type:'image/jpeg',size:100}],value:'selected',click(){this.clicked=true;}};
const context=vm.createContext({window:{uploadWizardFacade:async()=>({url:'https://example.test/new.jpg',storagePath:'facade/new.jpg'})},auth:{get currentUser(){return {uid};}},hasRole:()=>allowed,notif:(message)=>messages.push(message),projects:{a:{id:'a',...stored},b:{id:'b',name:'Project B'}},document:{getElementById:()=>input},x:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'),compressImage:file=>compressed(file),db:{},doc:(_,kind,id)=>({kind,id}),serverTimestamp:()=>1,renderHomePage(){},runTransaction:async(_,run)=>run({get:async target=>({exists:()=>true,data:()=>stored}),update:(target,value)=>{writes.push({target,value});stored={...stored,...value};}})});
vm.runInContext(code,context);const w=context.window;
(async()=>{
 assert.match(w.renderProjectFacadeThumbnail({name:'A',facadePhoto:{url:'https://example.test/a.jpg'}}),/<img/);
 assert.doesNotMatch(w.renderProjectFacadeThumbnail({facadePhoto:{url:'javascript:alert(1)'}}),/<img/);
 assert.match(w.renderProjectFacadeThumbnail({name:'<tag>',facadePhoto:{url:'https://example.test/a.jpg?x="'}}),/&lt;tag>/);
 w.chooseProjectFacade('a');assert.equal(input.clicked,true);assert.equal(input.dataset.projectId,'a');
 await w.updateProjectFacade({target:input});assert.equal(writes.length,1);assert.equal(writes[0].target.id,'a');assert.equal(stored.name,'Project A');assert.equal(stored.workTypes[0],'ev-charger');assert.deepEqual(Object.keys(writes[0].value).sort(),['facadePhoto','updatedAt','updatedBy']);
 allowed=false;await w.updateProjectFacade({target:input});assert.equal(writes.length,1);allowed=true;
 input.files=[{type:'application/pdf',size:100}];await w.updateProjectFacade({target:input});assert.equal(writes.length,1);input.files=[{type:'image/jpeg',size:100}];
 stored.facadePhoto={url:'https://example.test/concurrent.jpg'};await w.updateProjectFacade({target:input});assert.equal(writes.length,1);assert.match(messages.at(-1),/another device/);
 compressed=async()=>{uid='different-account';return {type:'image/jpeg'};};await w.updateProjectFacade({target:input});assert.equal(writes.length,1);assert.match(messages.at(-1),/Account changed/);
 assert.equal(w._facadeUpdating,null);assert.equal(input.value,'');
 console.log('PASS: app syntax; facade thumbnails and escaping; manager-only photo edits; pinned project; unchanged project data; concurrent-edit and account-change protection.');
})().catch(error=>{console.error(error);process.exitCode=1;});
