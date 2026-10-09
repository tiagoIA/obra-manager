const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm'),{chromium}=require('playwright');
(async()=>{
 const source=fs.readFileSync('public/unit-followup.js','utf8'),model=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
 const {cleanFollowUp,followUpKey,followUpView,followUpReport,hasFollowUp}=model;
 assert.equal(hasFollowUp({}),false);assert.equal(followUpReport({id:'empty'}),'');assert.equal(cleanFollowUp().status,'');assert.equal(followUpView({id:'empty'}).returnLabel,'');
 assert.throws(()=>cleanFollowUp({returnDate:'2026-02-30'}));assert.throws(()=>cleanFollowUp({status:'invented'}));
 assert.equal(followUpKey({preparation:{team:'',access:'pending'},linkedTaskIds:['b','a']}),followUpKey({linkedTaskIds:['a','b','a'],preparation:{access:'pending',team:''}}));
 const room={id:'roof',name:'Roof',projectId:'arlington',followUp:{status:'pending',situation:'Investigation complete; repair pending.',nextAction:'Replace cable',returnNeeded:true,preparation:{access:'pending',materials:'pending'},accessNote:'Coordinate hatch access.',linkedTaskIds:['t'],shoppingListIds:['l']}};
 const tasks=[{id:'t',roomId:'roof',name:'Replace cable',done:false}],lists=[{id:'l',name:'Roof materials',projectId:'arlington'}];
 assert.equal(followUpView(room,tasks).returnLabel,'Return required — to schedule');
 assert.equal(followUpView(room,[{...tasks[0],assignedDate:'2026-10-13'}]).returnLabel,'Linked work scheduled — 2026-10-13');
 const report=followUpReport(room,tasks,lists);for(const text of ['Observed access condition','Coordinate hatch access.','Roof materials','Return required — to schedule','Pending'])assert(report.includes(text));assert(!report.includes('Responsible:'));
 // Exercise the actual unit-report generator with follow-up and legacy content together.
 const appSource=fs.readFileSync('public/index.html','utf8'),nodes={'pdf-content':{innerHTML:''},'pdf-report':{classList:{add:()=>{}}}};
 const reportContext={window:{location:{origin:'https://test.local'},unitFollowUp:{report:r=>followUpReport(r,tasks,lists)}},rooms:{roof:room},projects:{arlington:{name:'Arlington'}},allTasks:Object.fromEntries(tasks.map(t=>[t.id,t])),roomNotesList:{},document:{getElementById:id=>nodes[id]},x:s=>String(s??''),evidenceRows:()=>[],evidenceReport:()=>''};
 vm.runInNewContext(appSource.slice(appSource.indexOf('window.generateUnitReport=(rid)=>{'),appSource.indexOf('window.generateReport=()=>')),reportContext);reportContext.window.generateUnitReport('roof');assert(nodes['pdf-content'].innerHTML.includes('Return required — to schedule'));assert(nodes['pdf-content'].innerHTML.includes('Coordinate hatch access.'));
 for(const integration of ['window.unitFollowUp.card(room)','window.unitFollowUp.overview(pr)','window.unitFollowUp.scheduleCards(','filtRooms.map(r=>window.unitFollowUp.report(r))'])assert(appSource.includes(integration));
 // Exercise the actual persistence adapter. It updates only followUp and guards concurrent edits.
 const app=fs.readFileSync('public/index.html','utf8'),start=app.indexOf('installUnitFollowUp({'),adapter=app.slice(start,app.indexOf('installProjectBrief({',start));let host,writes=[];
 let savedRoom={projectId:'arlington',scopeBrief:{before:'Keep this'},followUp:room.followUp};
 const context={installUnitFollowUp:h=>host=h,followUpKey,cleanFollowUp,rooms:{roof:{...room}},allTasks:{},shoppingLists:{},projects:{},planUsers:()=>[],notif:()=>{},window:{openDailyAssign:()=>{}},auth:{currentUser:{uid:'u'}},db:{},doc:(_,type,id)=>({type,id}),serverTimestamp:()=> 'timestamp',renderContent:()=>{},runTransaction:async(_,fn)=>fn({get:async()=>({exists:()=>true,data:()=>savedRoom}),update:(ref,patch)=>writes.push(patch)})};
 vm.runInNewContext(adapter,context);await host.save('roof',{},room.followUp);assert.deepEqual(Object.keys(writes[0]),['followUp']);assert.equal(writes[0].followUp.status,'');assert.equal(savedRoom.scopeBrief.before,'Keep this');
 savedRoom.followUp={...room.followUp,nextAction:'Changed remotely'};await assert.rejects(()=>host.save('roof',{},room.followUp),/Another person/);assert.equal(writes.length,1);
 // Existing matching tasks are reused; deterministic IDs avoid duplicate concurrent creations.
 Object.assign(context,{getDocs:async()=>({docs:[{id:'existing',data:()=>({name:'  replace   CABLE '})}]}),query:(...a)=>a,collection:()=>{},where:()=>{},crypto:require('node:crypto').webcrypto,TextEncoder});
 assert.equal(await host.task('roof','Replace cable',''), 'existing');
 let creates=0;context.getDocs=async()=>({docs:[]});context.runTransaction=async(_,fn)=>fn({get:async ref=>({exists:()=>ref.type==='rooms'||creates>0,data:()=>({projectId:'arlington'})}),set:()=>creates++});
 const a=await host.task('roof','New cable',''),b=await host.task('roof',' new   CABLE ','');assert.equal(a,b);assert.equal(creates,1);
 const browser=await chromium.launch({headless:true});try{for(const width of [390,1280]){
  const page=await browser.newPage({viewport:{width,height:844}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://followup.test/**',r=>r.fulfill({contentType:r.request().url().endsWith('.js')?'text/javascript':'text/html',body:r.request().url().endsWith('.js')?source:'<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:8px}.plan-modal-overlay{position:fixed;inset:0;padding:12px;background:#eee;display:flex;justify-content:center}.plan-modal-box{padding:14px}.m-inp{display:block;width:100%;box-sizing:border-box}.fl{display:block}button{min-height:40px}textarea{font:inherit}</style><div id="cards"></div>'}));
  await page.goto('https://followup.test/');await page.evaluate(async({room,tasks,lists})=>{
   const {installUnitFollowUp}=await import('/unit-followup.js');window.room=room;window.saved=[];window.failed=false;window.created=0;window.schedules=[];
   installUnitFollowUp({room:()=>window.room,data:()=>({tasks,lists,users:[{id:'u',name:'Technician'}],projects:[{id:'arlington',name:'Arlington'}]}),notify:()=>{},save:async(id,draft)=>{if(failed)throw Error('Connection failed.');saved.push(draft);window.room.followUp=draft;},task:async()=>{created++;return 't';},schedule:ids=>schedules.push(ids)});
  },{room:{...room,scopeBrief:{nextStep:'Confirm route and prepare purchases.'}},tasks,lists});
  await page.evaluate(()=>unitFollowUp.open('roof'));await page.getByRole('dialog',{name:'Unit follow-up'}).waitFor();
  await page.getByLabel('Responsible employee (optional)').selectOption('u');await page.getByLabel('Return date (optional)').fill('2026-10-13');await page.getByLabel('Team',{exact:true}).selectOption('ready');
  await page.getByLabel('New task name (optional)').fill('Replace cable');await page.getByRole('button',{name:'Create or reuse task and link'}).click();await page.getByText('Task created or reused and linked. Save follow-up to keep this link.').waitFor();
  await page.evaluate(()=>failed=true);await page.getByRole('button',{name:'Save follow-up',exact:true}).click();await page.getByText('Connection failed.',{exact:true}).waitFor();assert.equal(await page.getByLabel('Return date (optional)').inputValue(),'2026-10-13');
  await page.evaluate(()=>failed=false);await page.getByRole('button',{name:'Save follow-up',exact:true}).click();await page.waitForFunction(()=>saved.length===1);
  assert.equal(await page.evaluate(()=>saved[0].linkedTaskIds.length),1);assert.equal(await page.evaluate(()=>saved[0].preparation.access),'pending');
  await page.evaluate(()=>document.getElementById('cards').innerHTML=unitFollowUp.scheduleCards([room],'2026-10-13'));
  assert(await page.getByText('Return planned — 2026-10-13',{exact:true}).isVisible());assert(await page.getByText('Preparation pending: access, materials · execution remains available',{exact:true}).isVisible());
  await page.evaluate(()=>unitFollowUp.schedule('roof'));assert.deepEqual(await page.evaluate(()=>schedules[0]),['t']);
  await page.evaluate(()=>{room.followUp={};unitFollowUp.open('roof');});await page.getByRole('button',{name:'Save follow-up',exact:true}).click();await page.waitForFunction(()=>saved.length===2);assert.equal(await page.evaluate(()=>saved[1].returnDate),'');assert.equal(await page.evaluate(()=>saved[1].status),'');
  assert.equal(await page.evaluate(()=>unitFollowUp.report(room)),'');assert.equal(await page.evaluate(()=>unitFollowUp.scheduleCards([room],'2026-10-13')),'');
  await page.evaluate(()=>{room.followUp={returnNeeded:true};unitFollowUp.open('roof');});await page.getByRole('button',{name:'Save follow-up',exact:true}).click();await page.waitForFunction(()=>saved.length===3);assert.equal(await page.evaluate(()=>saved[2].returnDate),'');assert((await page.evaluate(()=>unitFollowUp.report(room))).includes('Return required — to schedule'));
  await page.evaluate(()=>unitFollowUp.open('roof'));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);await page.close();
 }}finally{await browser.close();}
 console.log('PASS: full/partial/empty optional follow-up, mobile/desktop, retry preserves entries, no inferred completion/date, task reuse and concurrent deduplication, guarded room-only save, dynamic task assignments, nonblocking readiness, purchases and reports.');
})().catch(e=>{console.error(e);process.exitCode=1;});
