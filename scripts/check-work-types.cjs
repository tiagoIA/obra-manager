const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('public/app.html','utf8');
const helpers=html.slice(html.indexOf('// Optional facade photograph'),html.indexOf('// ─── PROJECT WIZARD'));
const wizard=html.slice(html.indexOf('window.renderWizard=function'),html.indexOf('window.wizBack='));
const create=html.slice(html.indexOf('window.createProjectFromWizard=async'),html.indexOf('// Keep backward compat'));
const elements={'wizard-content':{},'proj-sel':{}};let saved;
const noop=()=>{};
const ctx=vm.createContext({window:{},document:{getElementById:id=>elements[id]},x:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'),materials:{},DEFAULT_TASKS:[],notif:noop,syncing:noop,setLoadMsg:noop,hideLoad:noop,closeModal:noop,renderRoomsList:noop,renderContent:noop,db:{},collection:(_,name)=>name,serverTimestamp:()=>1,addDoc:async(name,data)=>{assert.equal(name,'projects');saved=data;return {id:'new-project'};},activePid:null,activePage:'',URL:{revokeObjectURL:()=>{}},auth:{currentUser:{uid:'test-user'}},crypto:{randomUUID:()=> 'test-photo'},storage:{},ref:(_,path)=>path,uploadBytes:async()=>{},getDownloadURL:async()=> 'https://example.test/facade.jpg'});
vm.runInContext(helpers+wizard+create,ctx);
const w=ctx.window;
function reset(){w.wizData={name:'Test project',address:'Test address',type:'commercial',scope:'electrical',initialConditions:'Existing parking',workScope:'Install chargers',unitGroups:[],selectedTasks:[],spaces:{}};w.SPACE_TEMPLATES={};w.wizStep=2;}
(async()=>{
 reset();w.renderWizard();assert.match(elements['wizard-content'].innerHTML,/EV Charger/);assert.match(elements['wizard-content'].innerHTML,/OPTIONAL/);assert.doesNotMatch(elements['wizard-content'].innerHTML,/Fire alarm installation/);
 await w.createProjectFromWizard();assert.equal(saved.workTypes.length,0);assert.equal(saved.customWorkType,'');assert.equal(saved.type,'commercial');
 w.toggleWizWorkType('ev-charger',true);w.toggleWizWorkType('lighting',true);w.toggleWizWorkType('ev-charger',true);assert.equal(w.wizData.workTypes.length,2);
 w.wizData.customWorkType='  Custom <service>  ';w.wizStep=6;w.renderWizard();assert.match(elements['wizard-content'].innerHTML,/EV Charger, Lighting, Custom &lt;service>/);
 await w.createProjectFromWizard();assert.equal(saved.workTypes.join(','),'ev-charger,lighting');assert.equal(saved.customWorkType,'Custom <service>');
 w.wizData.type='residential';await w.createProjectFromWizard();assert.equal(saved.type,'residential');assert.equal(saved.workTypes[0],'ev-charger');
 w.setWizScope('fire');assert.equal(w.wizData.workTypes.length,0);w.toggleWizWorkType('ev-charger',true);assert.equal(w.wizData.workTypes.length,0);w.toggleWizWorkType('fire-alarm-installation',true);assert.equal(w.wizData.workTypes[0],'fire-alarm-installation');
 w.setWizScope('both');w.toggleWizWorkType('ev-charger',true);await w.createProjectFromWizard();assert.equal(saved.workTypes.length,2);
 w.toggleWizWorkType('ev-charger',false);assert.equal(w.wizData.workTypes.includes('ev-charger'),false);
 reset();w.wizData.customWorkType='Only custom';await w.createProjectFromWizard();assert.equal(saved.workTypes.length,0);assert.equal(saved.customWorkType,'Only custom');
 w.wizData.facadeBlob={type:'image/jpeg'};await w.createProjectFromWizard();assert.equal(saved.facadePhoto.url,'https://example.test/facade.jpg');assert.equal(saved.facadePhoto.uploadedBy,'test-user');assert.equal(w.wizData.facadeBlob,undefined);
 assert.equal(w.renderProjectFacade({}),'');assert.equal(w.renderProjectFacade({facadePhoto:{url:'javascript:alert(1)'}}),'');assert.match(w.renderProjectFacade(saved),/Front of the house/);
 const previous=saved;w.wizData.facadeProcessing=true;await w.createProjectFromWizard();assert.equal(saved,previous);assert.equal(w._projectCreating,false);
 w.wizData.facadeProcessing=false;w.wizData.facadeBlob={type:'image/jpeg'};ctx.uploadBytes=async()=>{throw Error('Upload unavailable');};await w.createProjectFromWizard();assert.equal(saved,previous);assert.equal(w._projectCreating,false);assert.ok(w.wizData.facadeBlob);
 console.log('PASS: facade present/absent, processing and failed upload guard, home rendering, and  optional blank/custom, multiple selections, scope changes, escaping, review, residential/commercial and actual project payload.');
})().catch(e=>{console.error(e);process.exit(1);});
