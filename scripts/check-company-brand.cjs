const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context=vm.createContext({URL,Date,console,setTimeout,clearTimeout});const modules=new Map();
async function get(path){if(modules.has(path))return modules.get(path);const m=new vm.SourceTextModule(fs.readFileSync(path,'utf8'),{context});modules.set(path,m);await m.link(s=>get('public/'+s.replace('./','')));return m;}
(async()=>{
 const m=await get('public/photo-report.js');await m.evaluate();
 const {buildPhotoModel,renderPhotoReport}=m.namespace;
 const source={project:{id:'arlington',name:'Arlington',companyId:'cfc-electric'},rooms:[],tasks:[],notes:[],company:{id:'cfc-electric',name:'CFC Electric',website:'cfcelectric.com',logoURL:'https://example.test/cfc.png'}};
 const before=JSON.stringify(source),model=buildPhotoModel(source);
 for(const complete of [false,true]){
  const html=renderPhotoReport(model,'en',complete);
  assert(html.includes('CFC Electric'));assert(html.includes('cfcelectric.com'));assert(html.includes('https://example.test/cfc.png'));
  assert(!html.includes('OBRA MANAGER · FIELD DOCUMENTATION'));
 }
 assert.throws(()=>buildPhotoModel({...source,company:{id:'pnv-electric',name:'PNV Electric'}}));
 const noLogo=renderPhotoReport(buildPhotoModel({...source,company:{id:'cfc-electric',name:'CFC Electric',logoURL:'javascript:alert(1)'}}));
 assert(noLogo.includes('CFC Electric'));assert(!noLogo.includes('javascript:'));assert(!noLogo.includes('pr-company-logo'));
 const escaped=renderPhotoReport(buildPhotoModel({...source,company:{id:'cfc-electric',name:'<script>alert(1)</script>'}}));
 assert(!escaped.includes('<script>alert'));assert.equal(JSON.stringify(source),before);
 console.log('PASS company report branding: Summary/Complete, identity mismatch denied, escaped company information, unsafe logo denied, name fallback, unchanged records.');
})().catch(e=>{console.error(e);process.exit(1)});
