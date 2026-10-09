// Covered jointly with scope, originals, continuous camera and offline recovery.
const fs=require('node:fs'),vm=require('node:vm');
for(const name of ['field-media.js','note-photos.js','project-brief.js'])new vm.SourceTextModule(fs.readFileSync('public/'+name,'utf8'));
console.log('PASS: evidence modules parse; behavior covered by check-brief.cjs.');
