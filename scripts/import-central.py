"""Prepare verified public catalog data; preserve IDs, stock and existing purchase links."""
import json,pathlib,re,hashlib,io,html,uuid,concurrent.futures,collections
from urllib.parse import quote,urlparse
import requests
from PIL import Image

PLACEHOLDERS={'1809524679fdd7d0b46d13d0aa2edb5ef818e9d3a619961e4e5f64ccaae00c77','d7ec0494f7d7c73468a7d4b5ec117b351741ea2a300bed9dcd99e5abfb71e42d'}
GENERIC_BRANDS={'multiple','conduitmetal','wirecopper','copperbuildingwire','datacom'}
def norm(v):return re.sub('[^a-z0-9]','',str(v or '').lower())
def decode(v):
 if 'stringValue' in v:return v['stringValue']
 if 'integerValue' in v:return int(v['integerValue'])
 if 'doubleValue' in v:return v['doubleValue']
 if 'booleanValue' in v:return v['booleanValue']
 if 'timestampValue' in v:return v['timestampValue']
 if 'arrayValue' in v:return [decode(x) for x in v['arrayValue'].get('values',[])]
 if 'mapValue' in v:return {k:decode(x) for k,x in v['mapValue'].get('fields',{}).items()}
 return None
def keys(p):
 result=[];upc=re.sub(r'\D','',str(p.get('upc') or ''))
 if re.fullmatch(r'\d{12,14}',upc) and int(upc)>0:result.append('upc:'+upc.lstrip('0'))
 brand=norm(p.get('brand'));part=norm(p.get('manufacturerPart'))
 if brand and part and brand not in GENERIC_BRANDS and part not in {'wire','na','nocat','emtx','pvc'} and not re.search('[,;]',p.get('brand','')):result.append('mpn:'+brand+':'+part)
 for s in p.get('suppliers') or []:
  if s.get('name') and s.get('code'):result.append('supplier:'+norm(s['name'])+':'+norm(s['code']))
 return result
def photograph(p):
 assert p['photoSha256'] not in PLACEHOLDERS
 u=urlparse(p['photoSourceUrl']);assert u.scheme=='https' and u.hostname
 r=requests.get(p['photoSourceUrl'],timeout=40);r.raise_for_status();assert len(r.content)<12_000_000
 im=Image.open(io.BytesIO(r.content));im.load();assert min(im.size)>=80
 im=im.convert('RGB');im.thumbnail((1000,1000));out=io.BytesIO();im.save(out,'JPEG',quality=86);raw=out.getvalue()
 assert hashlib.sha256(raw).hexdigest()==p['photoSha256'],'Photo changed since visual review; abort rather than import a new image'
 return raw
def prepare(s,fire,bucket,folder,material_docs,encode):
 products=json.loads(pathlib.Path('catalog-products-v1.json').read_text());assert 100<=len(products)<=200
 # Validate every image before any database write or hosting release.
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:photos=list(pool.map(photograph,products))
 originals={d['name']:d for d in material_docs};records={d['name']:{k:decode(v) for k,v in d.get('fields',{}).items()} for d in material_docs};changed={};new=set();imported=[];skipped=[]
 # GCE data already exists: retain its old internal SKU and all supplier metadata.
 for name,p in records.items():
  if p.get('isTask') or not p.get('gceCode'):continue
  suppliers=[dict(x) for x in p.get('suppliers') or []];ref=next((x for x in suppliers if x.get('name')=='Granite City Electric'),None)
  if ref is None:ref={'name':'Granite City Electric'};suppliers.append(ref)
  before=json.dumps(ref,sort_keys=True)
  if not ref.get('code'):ref['code']=str(p['gceCode'])
  if not ref.get('url') and p.get('sourceUrl'):ref['url']=p['sourceUrl']
  if not ref.get('unit'):ref['unit']=p.get('unit','un')
  if json.dumps(ref,sort_keys=True)!=before or suppliers!=(p.get('suppliers') or []):p['suppliers']=suppliers;changed.setdefault(name,set()).add('suppliers')
 gce_count=len(changed)
 for p,photo in zip(products,photos):
  p={**p,'name':html.unescape(p['name']).strip()};assert p['name'] and p['unit'] and p['sourceUrl'].startswith('https://')
  pkeys=set(keys(p));matches=[name for name,old in records.items() if not old.get('isTask') and pkeys.intersection(keys(old))]
  if len(matches)>1:skipped.append({'name':p['name'],'reason':'Ambiguous existing identity'});continue
  if matches:
   name=matches[0];old=records[name]
   if old.get('unit','un')!=p['unit']:skipped.append({'name':p['name'],'reason':'Order unit differs; needs review'});continue
   oldmpn=next((k for k in keys(old) if k.startswith('mpn:')),None);newmpn=next((k for k in pkeys if k.startswith('mpn:')),None)
   if oldmpn and newmpn and oldmpn!=newmpn:skipped.append({'name':p['name'],'reason':'UPC has conflicting manufacturer/model'});continue
   refs=[dict(x) for x in old.get('suppliers') or []]
   for ref in p['suppliers']:
    same=next((x for x in refs if x.get('name')==ref['name'] and str(x.get('code') or '')==ref['code']),None)
    if same is None:refs.append(dict(ref))
    else:
     for k,v in ref.items():
      if not same.get(k):same[k]=v
   if refs!=(old.get('suppliers') or []):old['suppliers']=refs;changed.setdefault(name,set()).add('suppliers')
   for field in ['brand','manufacturerPart','upc','specs','sourceUrl','family','subcategory','recordType']:
    if not old.get(field) and p.get(field):old[field]=p[field];changed.setdefault(name,set()).add(field)
  else:
   ident=hashlib.sha256('|'.join(sorted(pkeys)).encode()).hexdigest()[:20];name=fire.replace('https://firestore.googleapis.com/v1/','')+'/materials/catalog-'+ident
   assert name not in records,'Deterministic ID collision'
   sku='MAT-'+ident[:12].upper();assert not any(x.get('sku')==sku for x in records.values())
   old={k:v for k,v in p.items() if k not in ['source','photoSha256','photoSourceUrl','reviewNote']}
   old.update({'sku':sku,'isTask':False,'qty':0,'scope':'RC','description':'Referência de catálogo público. Confirmar aplicação, modelo e unidade antes da compra.','importBatch':folder})
   records[name]=old;new.add(name);changed[name]=set(old)
  if not old.get('photoUrl'):
   asset='materials/'+name.split('/')[-1]+'/catalog-'+p['photoSha256'][:12]+'.jpg';blob=bucket.blob(asset);token=str(uuid.uuid4());blob.metadata={'firebaseStorageDownloadTokens':token,'sourceUrl':p['photoSourceUrl'],'catalogBatch':folder}
   if not blob.exists():blob.upload_from_string(photo,content_type='image/jpeg',if_generation_match=0)
   else:blob.reload();token=blob.metadata.get('firebaseStorageDownloadTokens','')
   assert token
   old.update({'photoUrl':'https://firebasestorage.googleapis.com/v0/b/'+bucket.name+'/o/'+quote(asset,safe='')+'?alt=media&token='+token,'photoSourceUrl':p['photoSourceUrl'],'photoVerifiedAt':p['sourceVerifiedAt']})
   changed.setdefault(name,set()).update(['photoUrl','photoSourceUrl','photoVerifiedAt'])
  imported.append({'id':name.split('/')[-1],'name':p['name'],'sku':old['sku'],'manufacturerPart':old.get('manufacturerPart',''),'suppliers':p['suppliers'],'new':name in new,'photo':bool(old.get('photoUrl'))})
 writes=[]
 for name,fields in changed.items():
  if not fields:continue
  write={'update':{'name':name,'fields':{k:encode(records[name][k]) for k in fields}},'currentDocument':{'exists':False} if name in new else {'updateTime':originals[name]['updateTime']},'updateTransforms':[{'fieldPath':'updatedAt','setToServerValue':'REQUEST_TIME'}]}
  if name in new:write['updateTransforms'].append({'fieldPath':'createdAt','setToServerValue':'REQUEST_TIME'})
  else:write['updateMask']={'fieldPaths':sorted(fields)}
  writes.append(write)
 receipt={'candidatesReviewed':len(products),'newProducts':len(new),'existingGceSuppliersEnriched':gce_count,'existingProductsMatched':len(imported)-len(new),'skipped':skipped,'imported':imported,'families':dict(collections.Counter(p['family'] for p in products)),'sources':dict(collections.Counter(p['source'] for p in products))}
 bucket.blob(folder+'catalog-receipt.json').upload_from_string(json.dumps(receipt,ensure_ascii=False),content_type='application/json',if_generation_match=0)
 # Prepared writes have optimistic preconditions; one atomic commit in the release script.
 assert len(writes)<450
 print('CATALOG_PREPARED',json.dumps({k:v for k,v in receipt.items() if k not in ['imported','skipped']},ensure_ascii=False))
 print('CATALOG_SKIPPED',json.dumps(skipped,ensure_ascii=False))
 pathlib.Path('catalog-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
 return writes,originals

def rollback(s,fire,writes,result,originals):
 # Do not undo any edits made by a user after this deployment.
 undo=[]
 for write,res in zip(writes,result['writeResults']):
  name=write['update']['name'];condition={'updateTime':res['updateTime']}
  if name in originals:undo.append({'update':{'name':name,'fields':originals[name]['fields']},'currentDocument':condition})
  else:undo.append({'delete':name,'currentDocument':condition})
 r=s.post(fire+':commit',json={'writes':undo},timeout=60);r.raise_for_status();print('CATALOG_ROLLBACK_VERIFIED',len(undo))
