import assert from 'node:assert/strict';
import {referenceStore} from '../public/installation-reference-store.mjs';
let actor='admin',edit=true;const records={tasks:{t:{name:'Work',photos:['existing'],done:true}},installationReferences:{}};
const store=referenceStore({user:()=>actor,canEdit:()=>edit,newId:()=> 'guide',transaction:async fn=>fn({get:async(k,id)=>structuredClone(records[k][id]||null),set:(k,id,v)=>records[k][id]=v,update:(k,id,v)=>Object.assign(records[k][id],v)})});
let g=await store.save(null,{title:'Guide'});assert.equal(g.revision,1);assert.equal(records.installationReferences.guide.title,'Guide');
await store.link('t','guide',true);await store.link('t','guide',true);assert.deepEqual(records.tasks.t.referenceIds,['guide']);assert.deepEqual(records.tasks.t.photos,['existing']);assert.equal(records.tasks.t.done,true);
await store.link('t','guide',false);assert.deepEqual(records.tasks.t.referenceIds,[]);
await assert.rejects(store.save('guide',{...g,revision:0}),/changed/);edit=false;await assert.rejects(store.save('guide',g),/administrators/);actor='';await assert.rejects(store.link('t','guide',true),/Sign in/);
console.log('Reference persistence adapter checks passed');
