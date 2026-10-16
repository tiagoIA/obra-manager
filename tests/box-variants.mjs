import assert from 'node:assert/strict';
import fs from 'node:fs';
import {attributeValues,facetKeys,validateAttributes,declaredVariantAttributes} from '../public/material-attributes.js';
import {filterCatalog} from '../public/shopping-catalog.js';
import {validateProduct,productKeys} from '../public/central-catalog-v1.js';
const rows=[
 {id:'pvc14',name:'PVC old work box',catalogFamily:'boxes',boxMaterial:'PVC',boxVolume:14,boxDepth:2.75,gangs:1,workType:'Old Work'},
 {id:'pvc20',name:'PVC old work box',catalogFamily:'boxes',boxMaterial:'PVC',boxVolume:20,boxDepth:3.65,gangs:1,workType:'Old Work'},
 {id:'steel',name:'4 in square box',catalogFamily:'boxes',boxMaterial:'Steel',boxVolume:30.3,boxDepth:2.125,gangs:0},
 {id:'unknown',name:'Box without volume',catalogFamily:'boxes'},
];
assert.deepEqual(filterCatalog(rows,{family:'boxes',boxVolume:'20 cu. in.'}).map(x=>x.id),['pvc20']);
assert.deepEqual(filterCatalog(rows,{family:'boxes',boxDepth:'2-1/8 in.'}).map(x=>x.id),['steel']);
assert.deepEqual(attributeValues(rows[2],'gangs'),['0']);
assert.deepEqual(attributeValues(rows[3],'boxVolume'),[]);
assert(facetKeys('boxes').includes('boxDepth'));
assert(!facetKeys('cable').includes('boxVolume'));
assert(facetKeys('cable').includes('wireType'));
assert.deepEqual(declaredVariantAttributes({catalogFamily:'cable',name:'250 ft 12/2 Solid Copper NM-B Cable'}).wireType,['NM-B']);
assert.deepEqual(declaredVariantAttributes({catalogFamily:'fittings',name:'1/2 in Steel EMT Compression Connector'}).connectionType,['Compression']);
assert.deepEqual(declaredVariantAttributes({catalogFamily:'lighting',name:'6 in. Round Recessed 12 W 900 Lumens 3000K LED'}).diameter,['6 in.']);
assert.equal(declaredVariantAttributes({catalogFamily:'lighting',name:'100 Watt Equivalent LED'}).wattage,undefined);
assert.throws(()=>validateAttributes({boxVolume:-1}));
assert.throws(()=>validateAttributes({gangs:1.5}));
const data=JSON.parse(fs.readFileSync('catalog-expansion/box-products.json'));
const seen=new Set();for(const m of data.materials){validateProduct(m,[]);for(const k of productKeys(m)){assert(!seen.has(k));seen.add(k);}assert(m.photoUrl&&m.sourceUrl&&m.brand&&m.manufacturerPart);}
for(const r of data.updates){assert(r.id&&r.identity&&r.sourceUrl);validateAttributes(r.attributes);}
const app=fs.readFileSync('public/app.html','utf8');for(const key of ['boxVolume','boxDepth','gangs','wireType','connectionType','diameter'])assert(app.slice(app.indexOf('const keys=')).includes("'"+key+"'"));
console.log('PASS box volume/depth isolation, unknown capacity, gang zero, family-specific filters, source label extraction and '+data.materials.length+' native product candidates');
