"""Read catalog identities only; no writes and no invoice history."""
import json, os, pathlib
import firebase_admin
from firebase_admin import credentials, firestore
key=json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id')!='obra-manager-4ecc7':raise ValueError('Unexpected Firebase project')
firebase_admin.initialize_app(credentials.Certificate(key)); db=firestore.client()
fields=['name','brand','manufacturerPart','model','upc','cat','catalogFamily','family','unit','photoUrl','packQuantity','packUnit','recordType','active','status','suppliers']
rows=[]
for doc in db.collection('materials').stream():
 data=doc.to_dict()
 if data.get('isTask'):continue
 rows.append(dict(id=doc.id,**{k:data[k] for k in fields if k in data}))
active=[r for r in rows if r.get('active') is not False and r.get('status')!='inactive']
report={'totalNonTaskRecords':len(rows),'activeRecords':len(active),'activeSpecificProducts':sum(r.get('recordType')!='family' for r in active),'withPhoto':sum(bool(r.get('photoUrl')) for r in active),'targetMinimum':3000,'liveWrites':0,'materials':rows}
pathlib.Path('catalog-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
print(json.dumps({k:v for k,v in report.items() if k!='materials'}))
