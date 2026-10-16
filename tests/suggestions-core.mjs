import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {suggestionNeeds,applySuggestion,validateAccessoryRelations,nominalBox} from '../public/purchase-suggestions.js';
const mats=[
 {id:'switch',name:'15A Toggle Switch',catalogFamily:'devices',unit:'ea'},
 {id:'plate',name:'1-Gang Toggle Wall Plate',catalogFamily:'devices',gangs:1,unit:'ea'},
 {id:'decora',name:'1-Gang Decora Wall Plate',catalogFamily:'devices',gangs:1,unit:'ea'},
 {id:'plate2',name:'2-Gang Toggle Wall Plate',catalogFamily:'devices',gangs:2,unit:'ea'},
 {id:'box',name:'4 in. Square Steel Box',catalogFamily:'boxes',boxMaterial:'Steel',unit:'ea'},
 {id:'pvcbox',name:'Non-Metallic PVC Outlet Box',catalogFamily:'boxes',boxMaterial:'PVC',unit:'ea'},
 {id:'cover',name:'4 in. Square Blank Cover',catalogFamily:'boxes',unit:'ea'},
 {id:'ring',name:'4 in. Square Mud Ring',catalogFamily:'boxes',unit:'ea'},
 {id:'coverLarge',name:'4-11/16 in. Square Blank Cover',catalogFamily:'boxes',unit:'ea'},
 {id:'emt',name:'3/4 in. EMT Conduit',catalogFamily:'conduit',unit:'stick'},
 {id:'emtconn',name:'3/4 in. EMT Connector',catalogFamily:'fittings',unit:'ea'},
 {id:'pvcconn',name:'3/4 in. PVC Adapter',catalogFamily:'fittings',unit:'ea'},
 {id:'halfconn',name:'1/2 in. EMT Connector',catalogFamily:'fittings',unit:'ea'},
 {id:'cable',name:'12-2 NM-B Cable',catalogFamily:'cable',unit:'roll'},
 {id:'light',name:'Recessed LED Fixture',catalogFamily:'lighting',unit:'ea'}
];
const item=id=>({matId:id,name:mats.find(m=>m.id===id).name,qty:4,unit:mats.find(m=>m.id===id).unit,roomId:'r1'});
let items=[item('switch')],needs=suggestionNeeds(items,mats),plate=needs.find(n=>n.ruleId==='device-plate');assert.equal(plate.context.opening,'toggle');assert.ok(plate.missing.includes('Plate gangs'));let answers={[plate.key]:{opening:'toggle',gangs:'1'}};plate=suggestionNeeds(items,mats,answers).find(n=>n.ruleId==='device-plate');assert.deepEqual(plate.candidates.map(m=>m.id),['plate']);assert.throws(()=>applySuggestion(items,plate,mats[1],2),/Confirm/);applySuggestion(items,plate,mats[1],2,{acknowledged:true});assert.equal(items.length,2);assert.equal(items[1].bought,false);assert.equal(items[1].roomId,'r1');assert.equal(items[1].suggestionSource.ruleId,'device-plate');plate=suggestionNeeds(items,mats,answers).find(n=>n.ruleId==='device-plate');assert.equal(plate.existing.length,1);assert.throws(()=>applySuggestion(items,plate,mats[1],3,{acknowledged:true}),/Already/);applySuggestion(items,plate,mats[1],3,{acknowledged:true,adjustExisting:true});assert.equal(items[1].qty,3);assert.equal(items.length,2);items[1].bought=true;assert.throws(()=>applySuggestion(items,plate,mats[1],5,{acknowledged:true,adjustExisting:true}),/purchased/);
let box=suggestionNeeds([item('box')],mats).find(n=>n.ruleId==='box-finish');answers={[box.key]:{use:'junction'}};box=suggestionNeeds([item('box')],mats,answers).find(n=>n.ruleId==='box-finish');assert.deepEqual(box.candidates.map(m=>m.id),['cover']);assert.ok(!suggestionNeeds([item('pvcbox')],mats).some(n=>n.ruleId==='box-ground'));assert.equal(nominalBox(mats.find(m=>m.id==='coverLarge')),'square:4-11/16');
let conduit=suggestionNeeds([item('emt')],mats).find(n=>n.ruleId==='conduit-connector');assert.deepEqual(conduit.missing,[]);assert.deepEqual(conduit.candidates.map(m=>m.id),['emtconn']);assert.ok(suggestionNeeds([item('cable')],mats).some(n=>n.ruleId==='cable-termination'));assert.ok(suggestionNeeds([item('light')],mats).some(n=>n.ruleId==='lighting-mount'));assert.equal(suggestionNeeds([{name:'Written item',qty:1,unit:'ea'}],mats).length,0);
const custom={...mats[0],accessoryRelations:[{materialId:'plate',label:'Finish',group:'finish'},{materialId:'decora',label:'Finish',group:'finish'}]};let cs=suggestionNeeds([item('switch')],[custom,...mats.slice(1)]).filter(n=>n.ruleId==='product-relation');assert.equal(cs.length,1);assert.equal(cs[0].candidates.length,2);assert.throws(()=>validateAccessoryRelations({...custom,id:'switch',accessoryRelations:[{materialId:'plate',included:true}]},mats),/source/);
const before=JSON.stringify(mats);suggestionNeeds(items,mats,answers);assert.equal(JSON.stringify(mats),before);assert.throws(()=>applySuggestion(items,conduit,mats.find(m=>m.id==='pvcconn'),1,{acknowledged:true}),/no longer/);
new vm.SourceTextModule(fs.readFileSync('public/app.html','utf8').split('<script type="module">')[1].split('</script>')[0]);
console.log('PASS: switch plates, mutually exclusive box finishes, conduit type/size, cable and lighting needs, missing details, exact duplicate/quantity handling, purchased-line protection, room scope, custom alternative groups, immutable catalog and app syntax.');
