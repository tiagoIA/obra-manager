import os,json,re,hashlib
from pathlib import Path
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
seeds=json.loads(Path('scripts/catalog_seed.json').read_text());docs={d.id:d.to_dict() for d in db.collection('materials').stream()}
def norm(v):return re.sub('[^a-z0-9]','',str(v or '').lower())
def brand(v):
 n=norm(v)
 if n in ['firelite','firelitealarmshoneywell','firelitealarmsbyhoneywell']:return 'firelite'
 return n
resolved={};changes=[];before_qty={}
for seed in seeds:
 p=dict(seed);k=p.pop('key');target=p.pop('id',None)
 if k=='mmf300':target='6QaMLvEhgikzaNcroCTZ'
 if target:assert target in docs,'Existing target missing: '+k
 else:
  candidates=[mid for mid,m in docs.items() if not m.get('isTask') and brand(m.get('brand'))==brand(p['brand']) and norm(m.get('manufacturerPart'))==norm(p['manufacturerPart'])]
  assert len(candidates)<=1,'Ambiguous existing product: '+k
  target=candidates[0] if candidates else 'verified-purchase-'+k+'-20261009'
 old=docs.get(target,{})
 if old:before_qty[target]=old.get('qty')
 # Keep existing name, stock, active state, photos and historical references.
 if old:
  p.pop('name',None)
  if old.get('photoUrl'):p.pop('photoUrl',None)
  p['aliases']=list(dict.fromkeys([*old.get('aliases',[]),*p.get('aliases',[]),seed['name']]))
  refs=[dict(s) for s in old.get('suppliers',[])]
  for incoming in p['suppliers']:
   found=next((s for s in refs if norm(s.get('name'))==norm(incoming['name']) and (not s.get('code') or norm(s.get('code'))==norm(incoming['code']))),None)
   if found is None:refs.append(incoming)
   else:
    # Existing quotes/receipt prices dated later take precedence.
    if found.get('priceDate','')>incoming.get('priceDate',''):incoming={a:b for a,b in incoming.items() if a not in ['price','priceDate','priceSource','priceNote']}
    found.update(incoming)
  p['suppliers']=refs
 else:p.update(isTask=False,qty=0,active=True,status='active',sku='REF-'+k.upper(),createdAt=firestore.SERVER_TIMESTAMP)
 if not p.get('photoUrl') and not old.get('photoUrl'):p['photoReferenceNote']='Exact product photo still needs verification; use the linked supplier page.'
 p['updatedAt']=firestore.SERVER_TIMESTAMP
 resolved[k]=target;changes.append((db.collection('materials').document(target),p,bool(old)))
# Correct source conflicts without substituting a different product.
flags={
 'skFOYfd8DIfl8OlW2upd':('The source lists SMCO/SMICO-210 as 120 V. Verified SMCO210 is a sealed-battery alarm; identify the actual label before selecting a 120 V replacement.','Alarm model and supply conflict — identify before purchase.'),
 'muXoxFy3fyB2Uae04IE4':('The source lists SMCO/SMICO-210 as 120 V. Verified SMCO210 is a sealed-battery alarm; identify the actual label before selecting a 120 V replacement.','Alarm model and supply conflict — identify before purchase.'),
 'vkIv9XEz6Az7A7x3mM7m':('Source B300-16 white appears to refer to a detector mounting base, not wire. Confirm the exact label and compatible detector; do not substitute B300-6 automatically.','Detector mounting base — exact model pending.')}
for mid,(reason,desc) in flags.items():
 assert mid in docs;before_qty[mid]=docs[mid].get('qty');changes.append((db.collection('materials').document(mid),dict(catalogReviewStatus='needs-identification',catalogReviewReason=reason,description=desc,specs='Exact model and compatibility pending verification.',updatedAt=firestore.SERVER_TIMESTAMP),True))
# Audit evidence stays in existing product records. Unverified placeholder codes cannot auto-match.
placeholder='mRna05CM1Tyl21E9RSeG'
if placeholder in docs:
 refs=[{**s,'matchVerified':False,'verificationNote':'Existing unverified placeholder; confirm supplier code and price.'} for s in docs[placeholder].get('suppliers',[])]
 changes.append((db.collection('materials').document(placeholder),{'suppliers':refs,'catalogReviewStatus':'needs-identification','catalogReviewReason':'Generic relay with unverified supplier codes; choose a verified manufacturer/model.'},True));before_qty[placeholder]=docs[placeholder].get('qty')
# Verify the entire update atomically against the source records to avoid overwriting concurrent edits.
@firestore.transactional
def apply(tx):
 snapshots=[ref.get(transaction=tx) for ref,p,exists in changes]
 for snap,(ref,p,exists) in zip(snapshots,changes):
  if exists:assert snap.to_dict()==docs[ref.id],'Concurrent catalog edit: '+ref.id
  else:assert not snap.exists,'New product ID appeared; re-read before retrying'
 for ref,p,exists in changes:
  if exists:tx.update(ref,p)
  else:tx.create(ref,p)
apply(db.transaction())
# Guided image templates: preserve source quantities and historical prices.
links1={2:'hwllf',6:'pc2rled',7:'srled',8:'p2rled',9:'sgrkled',10:'lensr3',11:'sd365co',12:'bg12lx',13:'ann80',14:'sd365',15:'es50x',16:'mdf300',17:'mmf300',18:'crf300'}
links2={0:'hwllf',1:'p2rled',2:'sgrkled',3:'bg12lx',4:'sd365',5:'es50x',6:'mdf300',7:'mmf300',8:'battery1272',9:'elockfa',10:'ssm246',11:'wbb',12:'hcwllf'}
for lid,links in [('guided-reference-fa-scope-20261009',links1),('guided-reference-fa-quote-20261009',links2)]:
 ref=db.collection('shoppingLists').document(lid);snap=ref.get();assert snap.exists
 current=snap.to_dict();items=current['items'];assert len(items)==(23 if 'scope' in lid else 13)
 for n,k in links.items():
  items[n]['matId']=resolved[k]
  old_note=items[n].get('obs','');historical=old_note[old_note.find('Historical unit price'):] if 'Historical unit price' in old_note else ''
  items[n]['obs']=('Manufacturer/model and supplier code verified in the catalog. '+historical).strip()
  if k=='hcwllf':items[n]['obs']='Source reads BK-HCWLLE; verified model HCWL-LF / BK-HCWLLF. Confirm the supplied label and availability. '+historical
  if k=='elockfa':items[n]['obs']='Verified ELOCK-FA kit; ADI code O6-ELOCKFA starts with letter O, not zero. Verify breaker fit. '+historical
 if 'scope' in lid and 'Verify the model and supply noted in the source.' not in items[1].get('obs',''):items[1]['obs']=(items[1].get('obs','')+' Verify the model and supply noted in the source.').strip()
 ref.update({'items':items,'supplierReviewNote':'BK / FL codes verified against ADI references. Undated source prices are historical and are not current estimates. Some source model names require confirmation.','updatedAt':firestore.SERVER_TIMESTAMP})
# Rooftop checklist has unknown equipment quantities; it cannot be ordered without review.
lid='guided-arlington-roof-20261009';ref=db.collection('shoppingLists').document(lid)
if not ref.get().exists:
 names=[('HVAC disconnect — select rating and enclosure',None,'Specify one for each confirmed unit; verify nameplates and existing feeds.'),('Liquidtight whip / conduit and conductors — specified assembly',None,'Measure each run; verify gauge, conductor count, grounding and fittings. Catalog examples are not automatic selections.'),('Liquidtight connectors and seals',None,'Verify straight / angle fittings, trade size and included whip accessories.'),('Outdoor outlets — specified circuit rating',2,'Existing circuit is already on the roof. Verify protection, grounding and suitable outdoor device.'),('Weatherproof outlet boxes and extra-duty in-use covers',2,'Use separate components or complete kits; avoid buying both.'),('Mounting hardware and supports',None,'Check mounting surface, supports, corrosion resistance and existing brackets.'),('Grounding / bonding accessories',None,'Confirm actual existing bonding and specified equipment connections.'),('Circuit and disconnect labels',None,'Record panel, breaker and matching HVAC unit before final identification.')]
 items=[{'name':name,'matId':None,'cat':'eletrica','unit':'un','qty':qty,'obs':obs,'bought':False,'boughtAt':None} for name,qty,obs in names]
 ref.create({'name':'Roof — HVAC connections','note':'Arlington rooftop scope: check existing circuits, install disconnects and liquidtight connections, and install two outlets. Confirm equipment specifications before buying.','listType':'template','ownerUid':'zGxpaT3jW5S860Z49dma1FjINVJ2','projectId':None,'useIds':['hvac','devices'],'items':items,'questions':['HVAC unit count, nameplate voltage / MCA / MOCP and feed verification','Measured liquidtight runs, fitting sizes and supplied accessories','Outlet circuit rating, protection and existing boxes'],'version':1,'done':False,'createdAt':firestore.SERVER_TIMESTAMP})
for mid,qty in before_qty.items():assert db.collection('materials').document(mid).get().to_dict().get('qty')==qty,'Stock changed unexpectedly'
for k,mid in resolved.items():assert db.collection('materials').document(mid).get().to_dict()['manufacturerPart']==next(p['manufacturerPart'] for p in seeds if p['key']==k)
print('CATALOG_VERIFIED '+json.dumps({'verifiedProducts':len(resolved),'homeDepotElectrical':sum(p['cat']=='eletrica' for p in seeds),'preservedExistingStock':len(before_qty),'sourceTemplates':2,'roofChecklist':True,'modelsFlagged':len(flags),'products':resolved}))

coverage={}
for snap in db.collection('materials').stream():
 m=snap.to_dict()
 if m.get('isTask') or m.get('active') is False or m.get('status')=='inactive':continue
 for name in set(s.get('name','') for s in m.get('suppliers',[]) if s.get('matchVerified') is not False and (s.get('url') or (s.get('code') and norm(s.get('code'))!='0'))):coverage[name]=coverage.get(name,0)+1
print('SUPPLIER_COVERAGE '+json.dumps(coverage,sort_keys=True))
