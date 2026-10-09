const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('public/index.html', 'utf8');
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m => !/\bsrc=/.test(m[1]));
(async () => {
  for (const [i, m] of scripts.entries()) {
    if (/type=["']module/.test(m[1])) new vm.SourceTextModule(m[2]);
    else new vm.Script(m[2], {filename: `inline-${i}.js`});
  }
  const store = new Map();
  const context = vm.createContext({currentUser: {uid:'user-a'}, localStorage: {
    getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)
  }});
  const helpers = html.slice(html.indexOf('function recentProjectKey()'),html.indexOf('function installPhotoZoom('));
  vm.runInContext(helpers,context);
  vm.runInContext("['a','b','c','a','d'].forEach(rememberRecentProject)",context);
  assert.equal(vm.runInContext('JSON.stringify(getRecentProjects())',context),'["d","a","c"]');
  vm.runInContext("currentUser.uid='user-b'",context);
  assert.equal(vm.runInContext('JSON.stringify(getRecentProjects())',context),'[]');
  vm.runInContext("localStorage.setItem(recentProjectKey(),'broken')",context);
  assert.equal(vm.runInContext('JSON.stringify(getRecentProjects())',context),'[]');
  assert(!html.includes('activePid=Object.keys(projects)[0]'));
  const work = html.slice(html.indexOf('window.goWork=()=>{'),html.indexOf('window.openDashboard=()=>{'));
  let notified=false, opened=false;
  const guardContext=vm.createContext({window:{openHomePage:()=>opened=true},activePid:null,projects:{},notif:()=>notified=true,document:{querySelector:()=>null}});
  vm.runInContext(work,guardContext);guardContext.window.goWork();
  assert(opened&&notified);
  assert(!html.includes('user-scalable=no'));
  assert(!html.includes('// pinch\n'));
  for (const line of html.split('\n')) {
    if (line.includes('<img ') && (/phtml\+=|t\.photos\.map\(src/.test(line))) assert(!line.includes('object-fit:cover'));
  }
  // Execute gesture handlers against a small DOM mock: pinch, pan, reset and limits.
  const nodes=[];
  const document={createElement:()=>{const n={style:{},children:[],clientWidth:300,clientHeight:300,appendChild(c){this.children.push(c)},setAttribute(){}};nodes.push(n);return n;}};
  const overlay={querySelector:()=>null,appendChild(){}};
  const img={style:{},offsetWidth:200,offsetHeight:200,replaceWith(){}};
  const zoomContext=vm.createContext({document});
  vm.runInContext(html.slice(html.indexOf('function installPhotoZoom('),html.indexOf('window.openPhotoFullscreen=function')),zoomContext);
  zoomContext.installPhotoZoom(overlay,img);
  const stage=nodes[0];let prevented=0;
  const event=(a,b)=>({touches:[{clientX:a,clientY:0},{clientX:b,clientY:0}],preventDefault(){prevented++}});
  stage.ontouchstart(event(0,100));stage.ontouchmove(event(0,200));
  assert(img.style.transform.includes('scale(2)'));assert.equal(prevented,2);
  stage.ontouchend({touches:[{clientX:10,clientY:10}]});
  stage.ontouchmove({touches:[{clientX:50,clientY:30}],preventDefault(){}});
  assert(img.style.transform.includes('translate(40px,20px)'));
  stage.ondblclick({preventDefault(){}});
  assert.equal(img.style.transform,'translate(0px,0px) scale(1)');
  console.log(`PASS: ${scripts.length} inline scripts parse; recent projects, user isolation, Work guard, pinch/pan/reset, report image fit.`);
})();
