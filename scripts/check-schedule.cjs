const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('public/index.html','utf8');
const code=html.slice(html.indexOf('// ── DAILY / WEEKLY PLANNING'),html.indexOf('// Assign modal',html.indexOf('// ── DAILY / WEEKLY PLANNING')));
let manager=true,fail=false,writes=[],txWrites=[];
const ctx={console,Date,Set,Map,crypto:require('node:crypto').webcrypto,
 x:s=>String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'),
 currentUser:{uid:'u1'},currentProfile:{name:'Alex'},projects:{p1:{id:'p1',name:'Site A',address:'A'},p2:{id:'p2',name:'Site B',address:'B'}},rooms:{r1:{name:'Unit A'},r2:{name:'Unit B'}},allTasks:{},activePage:'planning',activePid:null,
 _cachedUsers:[{id:'u1',name:'Alex'},{id:'u2',name:'Sam'},{id:'inactive',active:false}],
 hasRole:()=>manager,notif:()=>{},syncing:()=>{},confirm:()=>false,navigator:{onLine:true},db:{},unsubs:{},collection:()=>{},onSnapshot:()=>()=>{},
 document:{getElementById:()=>null},doc:(_db,col,id)=>({col,id}),
 writeBatch:()=>{const staged=[];return {update:(ref,data)=>staged.push({ref,data}),commit:async()=>{if(fail)throw Error('denied');writes.push(...staged);}}},
 updateDoc:async(ref,data)=>{if(fail)throw Error('denied');writes.push({ref,data});},
 runTransaction:async(_db,fn)=>{if(fail)throw Error('denied');return fn({get:async ref=>({exists:()=>true,data:()=>({employeeSchedule:[{id:'concurrent',uid:'u2',startDate:'2026-10-09',endDate:'2026-10-09',address:'B'}]})}),update:(ref,data)=>txWrites.push({ref,data})});}
};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(code,ctx);
const run=s=>vm.runInContext(s,ctx);
(async()=>{
 assert(run("planValidDate('2026-10-09')"));assert(!run("planValidDate('2026-02-30')"));assert(!run("planValidDate('garbage')"));
 assert.equal(run("getPlanDateStr(new Date('2026-10-09T23:30:00-04:00'))"),'2026-10-09');
 ctx.allTasks={a:{id:'a',name:'Task A',projectId:'p1',roomId:'r1',assignedTo:'u1',assignedDate:'2026-10-09',plannedTime:'10:00',photos:['photo'],done:false},b:{id:'b',name:'Task B',projectId:'p2',roomId:'r2',assignedTo:'u1',assignedDate:'2026-10-09',plannedTime:'08:00'},c:{id:'c',name:'Task C',projectId:'p1',roomId:'r1',assignedTo:'u2',assignedDate:'2026-10-09'},d:{id:'d',name:'Pending',projectId:'p2',roomId:'r2',done:false},e:{id:'e',projectId:'p2',done:true}};
 run("_dailyDate='2026-10-09'");assert.equal(run('planDayTasks().length'),3);assert.equal(run('planDayTasks()[0].id'),'b');
 manager=false;assert.equal(run('planDayTasks().length'),2);assert(!run('planCanComplete(allTasks.c)'));assert.equal(await ctx.saveDailyAssignments(['d'],'u1','2026-10-09','',false),false);assert.equal(writes.length,0);
 const view={};ctx.renderPlanningPage(view);assert(view.innerHTML.includes('My Schedule'));assert(!view.innerHTML.includes('Pending work to distribute'));assert(!view.innerHTML.includes('data-daily-assign'));
 manager=true;ctx.renderPlanningPage(view);assert(view.innerHTML.includes('daily-employee'));assert(view.innerHTML.includes('Pending work to distribute'));assert(!view.innerHTML.includes('Select task" type="checkbox" checked'));
 fail=true;assert.equal(await ctx.saveDailyAssignments(['d'],'u1','2026-10-09','09:00',false,60),false);assert.equal(ctx.allTasks.d.assignedTo,undefined);assert.equal(run('_dailyBusy'),false);
 fail=false;assert.equal(await ctx.saveDailyAssignments(['d'],'u1','2026-10-09','09:00',false,60),true);assert.equal(ctx.allTasks.d.plannedMinutes,60);assert.equal(writes.at(-1).data.assignedTo,'u1');assert.deepEqual(ctx.allTasks.a.photos,['photo']);
 assert.equal(await ctx.saveDailyAssignments(['d'],'u1','2026-10-09','25:00',false),false);assert.equal(await ctx.saveDailyAssignments(['d'],'u1','2026-10-09','09:00',false,-1),false);
 assert.equal(await ctx.saveDailyAssignments(['d'],null,null,null,true),true);assert.equal(ctx.allTasks.d.assignedTo,null);
 const entry={id:'alloc',uid:'u1',address:'A',startDate:'2026-10-09',endDate:'2026-10-13',weekends:false,startTime:'07:00',note:''};
 assert(!ctx.planEntryOnDate(entry,'2026-10-10'));assert(ctx.planEntryOnDate(entry,'2026-10-12'));assert(!ctx.planEntryOnDate(entry,'2026-10-14'));
 assert.equal(await ctx.saveSiteSchedule('p1',entry),true);assert.equal(txWrites.at(-1).data.employeeSchedule.length,2);assert(ctx.projects.p1.employeeSchedule.some(e=>e.id==='concurrent'));
 manager=false;assert.equal(ctx.planSitesForDate('2026-10-09').length,1);assert(!ctx.planSiteCards('2026-10-09').includes('Edit days'));assert.equal(await ctx.saveSiteSchedule('p1',entry),false);
 assert.equal(await ctx.completeDailyTask('c'),false);assert.equal(await ctx.completeDailyTask('a'),true);assert.deepEqual(ctx.allTasks.a.photos,['photo']);assert(ctx.allTasks.a.done);
 console.log('PASS: local dates/DST, cross-project agenda, worker isolation, manager guards, atomic assignments, failed writes, photo preservation, multi-day allocations, weekends, concurrent allocation preservation.');
})().catch(e=>{console.error(e);process.exitCode=1;});
