import {updateGuide} from './installation-reference-core.mjs?v=20261022';
export function referenceStore(host){
 return {
  async save(id,input){const actor=host.user();if(!actor||!host.canEdit())throw Error('Only library administrators can save references.');const key=id||host.newId();return host.transaction(async tx=>{const previous=await tx.get('installationReferences',key);if(id&&!previous)throw Error('This guide is unavailable.');if(host.user()!==actor||!host.canEdit())throw Error('Account changed.');const data=updateGuide(previous,input,actor);tx.set('installationReferences',key,data);return {...data,id:key};});},
  async link(taskId,guideId,add){if(!host.user())throw Error('Sign in to link a guide.');const actor=host.user();return host.transaction(async tx=>{const task=await tx.get('tasks',taskId),guide=await tx.get('installationReferences',guideId);if(!task||!guide||add&&guide.status==='Archived')throw Error('The task or guide is unavailable.');if(host.user()!==actor)throw Error('Account changed.');const ids=new Set(task.referenceIds||[]);if(add)ids.add(guideId);else ids.delete(guideId);tx.update('tasks',taskId,{referenceIds:[...ids]});return [...ids];});}
 };
}
