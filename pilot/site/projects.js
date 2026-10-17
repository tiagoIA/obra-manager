import {collection,onSnapshot} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';
export function createProjectWorkspace({db,save,host}) {
  let unsubscribe, generation=0;
  function clear() { ++generation; unsubscribe?.(); unsubscribe=null; host.replaceChildren(); }
  function open(companyId,role) {
    clear(); const current=generation;
    const heading=document.createElement('h3'); heading.textContent='Company projects';
    const list=document.createElement('div'), message=document.createElement('p'); message.setAttribute('role','status');
    const form=document.createElement('form'); form.hidden=role!=='owner';
    const controls={}; let editing=null, saving=false, draftId=crypto.randomUUID();
    for (const [key,label,max] of [['name','Project name',120],['address','Address',500],['notes','Notes',4000]]) {
      const wrapper=document.createElement('label'); wrapper.textContent=label;
      const input=document.createElement(key==='notes'?'textarea':'input'); input.name=key; input.maxLength=max; input.required=key==='name'; if(key==='name')input.minLength=2;
      controls[key]=input; wrapper.append(input); form.append(wrapper);
    }
    const submit=document.createElement('button'); submit.textContent='Create project'; submit.type='submit';
    const cancel=document.createElement('button'); cancel.textContent='Cancel editing'; cancel.type='button'; cancel.hidden=true;
    function reset(){form.reset();editing=null;draftId=crypto.randomUUID();submit.textContent='Create project';cancel.hidden=true;}
    cancel.onclick=reset; form.append(submit,cancel);host.append(heading,form,message,list);
    async function persist(record,status) {
      if(saving)return;
      saving=true; form.inert=true; list.inert=true;message.textContent='Saving…';
      try {
        await save({projectId:record?.id||draftId,revision:record?.revision||0,name:controls.name.value,address:controls.address.value,notes:controls.notes.value,status});
        if(current!==generation)return;
        reset();message.textContent='Project saved.';
      } catch(error){if(current===generation)message.textContent=error.message||'Could not save project.';}
      finally{saving=false;if(current===generation){form.inert=false;list.inert=false;}}
    }
    form.onsubmit=event=>{event.preventDefault();persist(editing,editing?.status||'active');};
    unsubscribe=onSnapshot(collection(db,'companies',companyId,'projects'), snapshot=>{
      if(current!==generation)return;
      list.replaceChildren();
      if(snapshot.empty){const empty=document.createElement('p');empty.textContent='No projects yet. Create your first project above.';list.append(empty);}
      for(const item of snapshot.docs){
        const record={...item.data(),id:item.id};const card=document.createElement('article');
        const title=document.createElement('h4');title.textContent=record.name+(record.status==='archived'?' — Archived':'');
        const address=document.createElement('p');address.textContent=record.address||''; const notes=document.createElement('p');notes.textContent=record.notes||'';card.append(title,address,notes);
        if(role==='owner'){
          const edit=document.createElement('button');edit.type='button';edit.textContent='Edit project';edit.onclick=()=>{editing=record;for(const k in controls)controls[k].value=record[k]||'';submit.textContent='Save project';cancel.hidden=false;};card.append(edit);
          if(record.status!=='archived'){
            const archive=document.createElement('button');archive.type='button';archive.textContent='Archive project';archive.onclick=()=>{if(!confirm('Archive this project?'))return;editing=record;for(const k in controls)controls[k].value=record[k]||'';persist(record,'archived');};card.append(archive);
          }
        }
        list.append(card);
      }
    },error=>{if(current===generation)message.textContent=error.message;});
  }
  return {open,clear};
}
