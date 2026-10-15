const fs=require('node:fs');
const CORE="// BEGIN PARTIAL WORK PROGRESS\nfunction workTaskFraction(task){\n  if(task?.done)return 1;\n  const subs=Array.isArray(task?.subtasks)?task.subtasks.filter(s=>s&&typeof s==='object'):[];\n  return subs.length?subs.filter(s=>s.done).length/subs.length:0;\n}\nfunction workProgressPct(tasks){\n  const list=Array.isArray(tasks)?tasks:[];\n  if(!list.length)return 0;\n  const value=list.reduce((sum,t)=>sum+workTaskFraction(t),0)/list.length;\n  return value>=1-Number.EPSILON?100:Math.min(99,Math.round(value*100));\n}\nwindow.workProgress={fraction:workTaskFraction,percent:workProgressPct};\n// END PARTIAL WORK PROGRESS\n";
function patchProgress(html){
const core=CORE;
function replace(a,b){if(!html.includes(a))throw Error('Missing expected code: '+a.slice(0,100));html=html.split(a).join(b);}
replace('function roomProg(rid){',core+'\nfunction roomProg(rid){');
const lists=['pTasks','projTasks','allT','tasks','filtTasks','elec','fire','fElec','fFire','pE','pF','elecT','fireT','rTasks','rt','flT','et','ft','pT','myToday'];
for(const list of lists){
 const escaped=list.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const re=new RegExp(escaped+'\\.length\\s*\\?Math\\.round\\([^;\\n]*?/'+escaped+'\\.length\\*100\\):0','g');
 html=html.replace(re,'workProgressPct('+list+')');
}
replace('totalTasks?Math.round(doneTasks/totalTasks*100):0','workProgressPct(projTasks)');
replace('total>0?Math.round(done/total*100):0','workProgressPct(tasks)');
replace('fTotal?Math.round(fDone/fTotal*100):0','workProgressPct(fTasks)');
replace('total?Math.round(done/total*100):0','workProgressPct(typeof ts!==\'undefined\'?ts:typeof allT!==\'undefined\'?allT:typeof rTasks!==\'undefined\'?rTasks:progs.flatMap(o=>roomTasks(o.r.id)))');
replace('pct:Math.round(done/total*100)','pct:workProgressPct(ts)');
replace('elecT?Math.round(elecD/elecT*100):0','workProgressPct(typeof elec!==\'undefined\'?elec:progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat===\'eletrica\'||t.cat===\'inspecao\'))');
replace('fireT?Math.round(fireD/fireT*100):0','workProgressPct(typeof fire!==\'undefined\'?fire:progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat===\'fire\'))');
replace('g.total?Math.round(g.done/g.total*100):0','workProgressPct(g.tasks||projTasks.filter(t=>t.name===g.name))');
replace('units.length?Math.round(flDone/units.length*100):0','workProgressPct(units.map(u=>u.task))');
replace('n.total?Math.round(n.done/n.total*100):0','workProgressPct(allP.filter(t=>t.name===n.name))');
replace('totalAll?Math.round(g.doneCount/totalAll*100):0','workProgressPct(allP.filter(t=>t.name===g.name&&t.cat===g.cat))');
replace('m.tasks.length?Math.round(m.doneTasks/m.tasks.length*100):0','workProgressPct(m.tasks)');
replace('tp?Math.round(data.done.length/tp*100):0','workProgressPct(data.done.concat(data.todo))');
replace('fw.t?Math.round(fw.d/fw.t*100):0','workProgressPct(filtTasks.filter(t=>(rooms[t.roomId]?.floor||\'Other\')===f))');
replace("if(prog){const done=updated.filter(s=>s.done).length;prog.textContent=done+'/'+updated.length;}","if(prog){const done=updated.filter(s=>s.done).length;prog.textContent=done+'/'+updated.length+' · '+workProgressPct([{subtasks:updated}])+'%';}");
replace("const subBadge=subs.length?'<span class=\"st-progress\" id=\"st-prog-'+t.id+'\">'+subDone+'/'+subs.length+'</span>':'';","const subBadge=subs.length?'<span class=\"st-progress\" id=\"st-prog-'+t.id+'\">'+subDone+'/'+subs.length+' · '+workProgressPct([t])+'%</span>':'';");
replace("  // Salvar no Firestore\n  updateDoc(doc(db,'tasks',tid),updateData).catch(err=>{console.error('toggleSubtask:',err);});","  if(!allDone&&task.done){allTasks[tid].done=false;allTasks[tid].doneAt=null;updateData.done=false;updateData.doneAt=null;}\n  // Refresh both fractional progress and the independent completed-task count.\n  renderRoomsList();renderContent();\n  if(dashOpen)renderDashboard(document.getElementById('dash-content'));\n  updateDoc(doc(db,'tasks',tid),updateData).catch(err=>{console.error('toggleSubtask:',err);notif('Could not save subtask. Reload to confirm its status.','e');});");
const fallback="workProgressPct(typeof ts!=='undefined'?ts:typeof allT!=='undefined'?allT:typeof rTasks!=='undefined'?rTasks:progs.flatMap(o=>roomTasks(o.r.id)))";
html=html.replace(fallback,'workProgressPct(allT)');
html=html.replace(fallback,'workProgressPct(progs.flatMap(o=>roomTasks(o.r.id)))');
html=html.replace(fallback,'workProgressPct(rTasks)');
html=html.replace("workProgressPct(typeof elec!=='undefined'?elec:progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat==='eletrica'||t.cat==='inspecao'))",'workProgressPct(elec)');
html=html.replace("workProgressPct(typeof fire!=='undefined'?fire:progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat==='fire'))",'workProgressPct(fire)');
html=html.replace("workProgressPct(typeof elec!=='undefined'?elec:progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat==='eletrica'||t.cat==='inspecao'))","workProgressPct(progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat==='eletrica'||t.cat==='inspecao'))");
html=html.replace("workProgressPct(typeof fire!=='undefined'?fire:progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat==='fire'))","workProgressPct(progs.flatMap(o=>roomTasks(o.r.id)).filter(t=>t.cat==='fire'))");
return html;
}
module.exports=patchProgress;
if(require.main===module){const p=process.argv[2]||'public/app.html';fs.writeFileSync(p,patchProgress(fs.readFileSync(p,'utf8')));}
