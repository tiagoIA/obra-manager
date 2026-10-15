const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('public/app.html','utf8');
const helpers=html.slice(html.indexOf('// Optional service classification;'),html.indexOf('// ─── PROJECT WIZARD'));
const wizard=html.slice(html.indexOf('window.renderWizard=function'),html.indexOf('window.wizBack='));
const create=html.slice(html.indexOf('window.createProjectFromWizard=async'),html.indexOf('// Keep backward compat'));
const elements={'wizard-content':{},'proj-sel':{}};let saved;
const noop=()=>{};
const ctx=vm.createContext({window:{},document:{getElementById:id=>elements[id]},x:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'),materials:{},DEFAULT_TASKS:[],notif:noop,syncing:noop,setLoadMsg:noop,hideLoad:noop,closeModal:noop,renderRoomsList:noop,renderContent:noop,db:{},collection:(_,name)=>name,serverTimestamp:()=>1,addDoc:async(name,data)=>{assert.equal(name,'projects');saved=data;return {id:'new-project'};},activePid:null,activePage:''});
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
 console.log('PASS: optional blank/custom, multiple selections, scope changes, escaping, review, residential/commercial and actual project payload.');
})().catch(e=>{console.error(e);process.exit(1);});
