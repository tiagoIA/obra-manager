"""Backed-up, atomic reviewed migration; preserve all historical material IDs and stock."""
import os,json,pathlib,re,collections
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
from importlib.machinery import SourceFileLoader
catalog=SourceFileLoader('catalog','scripts/import-central.py').load_module()
def enc(v):
 if v is None:return {'nullValue':None}
 if isinstance(v,bool):return {'booleanValue':v}
 if isinstance(v,str):return {'stringValue':v}
 if isinstance(v,int):return {'integerValue':str(v)}
 if isinstance(v,float):return {'doubleValue':v}
 if isinstance(v,list):return {'arrayValue':{'values':[enc(x) for x in v]}}
 return {'mapValue':{'fields':{k:enc(x) for k,x in v.items()}}}
def candidate_kind(name):
 for kind,pattern in [('breakers',r'\bbreaker\b'),('devices',r'\boutlet\b|\breceptacle\b|\bswitch\b|dimmer'),('boxes',r'\bbox\b|junction box'),('conduit',r'\bconduit\b|\bEMT\b'),('accessories',r'screw|washer|\bnut\b|threaded rod|staple|strut|nailing plate'),('grounding',r'grounding|ground rod'),('lighting',r'light|troffer|fixture|exit sign')]:
  if re.search(pattern,name,re.I):return kind
 return None
def lifecycle_patch(old,plan,records):
 assert all(old.get(k)==v for k,v in plan['expected'].items()),'Reviewed material changed; audit again'
 patch=dict(plan['fields'])
 if plan.get('generic'):
  kind=candidate_kind(old.get('name',''))
  candidates=[p for p in records.values() if kind and p.get('family',p.get('subcategory'))==kind and p.get('recordType')=='product' and p.get('brand') and p.get('manufacturerPart') and p.get('active') is not False and p.get('status')!='inactive']
  if candidates:
   # Candidates are choices to review, never an equivalence mapping or automatic relink.
   patch['replacementSearch']=kind;patch['replacementNote']='Review specific products in this family; candidates are not interchangeable. Historical references and stock remain on this record.'
   if float(old.get('qty') or 0)==0:patch.update(active=False,status='inactive')
   else:patch['catalogReviewReason']='Stock remains on this unidentified generic record. Identify the exact physical product before deactivating or allocating inventory.'
 return patch
def main():
 key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
 creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']);s=AuthorizedSession(creds)
 fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents';bucket=storage.Client(project=key['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app');folder='backups/catalog-lifecycle/'+os.environ['GITHUB_RUN_ID']+'/'
 def read(col):
  docs=[];token=None
  while True:
   params={'pageSize':1000}
   if token:params['pageToken']=token
   r=s.get(fire+'/'+col,params=params,timeout=60);r.raise_for_status();d=r.json();docs+=d.get('documents',[]);token=d.get('nextPageToken')
   if not token:return docs
 def save(name,data):bucket.blob(folder+name).upload_from_string(json.dumps(data,ensure_ascii=False),content_type='application/json',if_generation_match=0)
 snapshot={col:read(col) for col in ['materials','shoppingLists','shoppingItems','tasks','productDB','invoices','invoiceItems']}
 assert len(snapshot['materials'])==495,'Catalog changed; audit again'
 for col,docs in snapshot.items():save(col+'.json',docs)
 writes,originals=catalog.prepare(s,fire,bucket,folder,snapshot['materials'],enc)
 originals.update({d['name']:d for d in snapshot['shoppingLists']})
 prepared={w['update']['name']:w for w in writes}
 records={d['name']:{k:catalog.decode(v) for k,v in d.get('fields',{}).items()} for d in snapshot['materials']}
 for w in writes:
  records.setdefault(w['update']['name'],{}).update({k:catalog.decode(v) for k,v in w['update']['fields'].items()})
 def merge(name,patch):
  if not patch:return
  if name in prepared:
   w=prepared[name];w['update']['fields'].update({k:enc(v) for k,v in patch.items()})
   if 'updateMask' in w:w['updateMask']['fieldPaths']=sorted(set(w['updateMask']['fieldPaths'])|set(patch))
  else:
   prepared[name]={'update':{'name':name,'fields':{k:enc(v) for k,v in patch.items()}},'updateMask':{'fieldPaths':sorted(patch)},'currentDocument':{'updateTime':originals[name]['updateTime']},'updateTransforms':[{'fieldPath':'updatedAt','setToServerValue':'REQUEST_TIME'}]}
 archived=[];generic=[];translated=[]
 for plan in json.loads(pathlib.Path('catalog-lifecycle-review-v1.json').read_text()):
  name=fire.replace('https://firestore.googleapis.com/v1/','')+'/materials/'+plan['id'];old={k:catalog.decode(v) for k,v in originals[name].get('fields',{}).items()}
  patch=lifecycle_patch(old,plan,records);patch['catalogLifecycleReviewedAt']='2026-10-08';merge(name,patch)
  if patch.get('active') is False:archived.append({'id':plan['id'],'sku':old.get('sku'),'name':old.get('name'),'linkedReferences':plan['linkedReferences']})
  if plan.get('generic'):generic.append(plan['id'])
  if any(k in patch for k in ['name','description','specs']):translated.append(plan['id'])
 templates=0;template_pending=[]
 old_presets={p['id']:p for p in json.loads(pathlib.Path('guided-presets-v1.json').read_text())};new_presets={p['id']:p for p in json.loads(pathlib.Path('guided-presets-en-v6.json').read_text())}
 for d in snapshot['shoppingLists']:
  ident=d['name'].split('/')[-1];old={k:catalog.decode(v) for k,v in d.get('fields',{}).items()}
  if ident not in old_presets or old.get('ownerUid') or not old.get('isBuiltIn'):continue
  if any(old.get(k)!=old_presets[ident].get(k) for k in ['name','questions','items']):template_pending.append(ident);continue
  merge(d['name'],{k:new_presets[ident][k] for k in ['name','questions','items']});templates+=1
 writes=list(prepared.values());assert len(writes)<450
 save('prepared-writes.json',writes);result=None
 try:
  r=s.post(fire+':commit',json={'writes':writes},timeout=90);r.raise_for_status();result=r.json();save('commit-result.json',result)
  after=read('materials');after_lists=read('shoppingLists');all_after={d['name']:d for d in after+after_lists}
  before_ids={d['name'] for d in snapshot['materials']};assert before_ids<=set(all_after),'Historical material ID removed'
  new_ids={w['update']['name'] for w in writes if w['update']['name'] not in originals};assert len(after)==495+len(new_ids)
  for w in writes:
   name=w['update']['name'];actual=all_after[name]['fields'];differences=[k for k,v in w['update']['fields'].items() if k not in actual or catalog.decode(actual[k])!=catalog.decode(v)];assert not differences,'Saved fields differ: '+','.join(differences)
   if name in originals:
    mask=set(w['update']['fields'])|{'updatedAt'};before=originals[name].get('fields',{})
    assert {k:v for k,v in before.items() if k not in mask}=={k:v for k,v in actual.items() if k not in mask},'Protected stock/history field changed'
  values=[{k:catalog.decode(v) for k,v in d.get('fields',{}).items()} for d in after]
  receipt={'catalogCount':len(after),'newProducts':len(new_ids),'genericReviewed':len(generic),'genericDeactivated':len(archived),'englishMaterialRecords':len(translated),'englishBuiltInTemplates':templates,'customizedBuiltInTemplatesPending':template_pending,'activeMaterials':sum(p.get('active') is not False and p.get('status')!='inactive' for p in values),'photos':sum(bool(p.get('photoUrl')) for p in values),'missingPhotos':sum(not p.get('photoUrl') for p in values),'backup':folder,'archived':archived}
  save('receipt.json',receipt);save('pending-identification.json',[{'id':d['name'].split('/')[-1],'sku':p.get('sku'),'name':p.get('name'),'reason':p.get('catalogReviewReason') or 'Exact manufacturer/model/photo remains unconfirmed.'} for d,p in zip(after,values) if p.get('catalogReviewStatus')=='needs-identification' or not p.get('photoUrl')]);print('LIFECYCLE_VERIFIED',json.dumps(receipt,ensure_ascii=False))
 except Exception:
  if result:catalog.rollback(s,fire,writes,result,originals)
  raise
if __name__=='__main__':main()
