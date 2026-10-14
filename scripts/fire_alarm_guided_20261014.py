import os,json,re
from urllib.parse import urlparse
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
fields=['name','sku','cat','unit','brand','model','manufacturerPart','active','status','catalogReviewStatus','description','aliases','guidedUses']
pattern=re.compile(r'smi?100|sm.?co.?210|h.?cw?l.?lf|low.frequency|blank|homeline|pc2r|srled|p2r|sgrk|lens.?r3|sd365|bg.?12|ann.?80|es.?50|mdf.?300|mmf.?300|crf.?300|7.?ah|battery|b300|lock.*break|elock|ssm246|bell|wbb',re.I)
rows=[]
for d in db.collection('materials').stream():
 m=d.to_dict()
 if m.get('isTask') or not pattern.search(' '.join(str(m.get(k,'')) for k in ['name','model','manufacturerPart','aliases'])):continue
 row={'id':d.id,**{k:m[k] for k in fields if k in m},'hasPhoto':bool(m.get('photoUrl')),'photoHost':urlparse(m.get('photoUrl') or '').hostname,'suppliers':[{k:s.get(k) for k in ['name','code','url']} for s in m.get('suppliers',[])]}
 rows.append(row)
print('GUIDED_CATALOG_AUDIT',json.dumps(rows),flush=True)
for lid in ['guided-reference-fa-scope-20261009','guided-reference-fa-quote-20261009']:
 s=db.collection('shoppingLists').document(lid).get()
 if s.exists:
  m=s.to_dict();print('GUIDED_TEMPLATE_AUDIT',json.dumps({'id':lid,**{k:m.get(k) for k in ['name','ownerUid','listType','version','items','useIds','questions','note']}}),flush=True)
