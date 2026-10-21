// Drafts are separate from purchased lists until the user confirms the review.
export function draftPayload(draft){
 const keys=['name','note','projectId','supplier','mode','items','services','answers','suggestionAnswers','suggestionDismissed','editId','baseList','baseItems','draftOwnerUid'];
 return JSON.parse(JSON.stringify(Object.fromEntries(keys.filter(k=>draft[k]!==undefined).map(k=>[k,draft[k]]))));
}
export function createDraftSaver({save,status=()=>{},local=()=>{},delay=500}){
 let timer,flight=null,pending=null,blocked=false,lastSaved='';
 async function drain(){
  if(flight)return flight;
  flight=(async()=>{while(pending&&!blocked){const job=pending;pending=null;const payload=draftPayload(job.draft),signature=job.draft.draftId+JSON.stringify(payload);if(signature===lastSaved){status('Draft saved');continue;}status('Saving draft…');try{
    const result=await save(job.draft.draftId,payload,job.draft.draftRevision||0);
    lastSaved=signature;job.draft.draftRevision=result.revision;local(job.draft);status('Draft saved');
   }catch(e){if(!pending)pending=job;blocked=true;status('Saved on this device · cloud save failed. Retry',e);}}})();
  try{await flight;}finally{flight=null;}
 }
 return {schedule(draft){local(draft);if(!draft.items?.length&&!draft.draftRevision&&!flight&&!pending)return;pending={draft};blocked=false;clearTimeout(timer);status('Saving draft…');timer=setTimeout(drain,delay);},
  async flush(){clearTimeout(timer);blocked=false;await drain();if(blocked)throw Error('Draft is saved on this device, but could not sync. Retry before finishing.');},
  cancel(){clearTimeout(timer);pending=null;},get pending(){return !!pending;}};
}
