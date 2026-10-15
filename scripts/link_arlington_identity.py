import json,os
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account
PROJECT='obra-manager-4ecc7'
key=json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id')!=PROJECT:raise SystemExit('Unexpected Firebase project')
db=firestore.Client(project=PROJECT,credentials=service_account.Credentials.from_service_account_info(key))
projects=[s for s in db.collection('projects').stream() if s.to_dict().get('name')=='455 Massachusetts Ave, Arlington, MA']
if len(projects)!=1:raise SystemExit('Expected one Arlington project')
p=projects[0];pid=p.id
rooms={s.id:s for s in db.collection('rooms').where(filter=firestore.FieldFilter('projectId','==',pid)).stream()}
notes=[s for s in db.collection('roomNotes').stream() if s.to_dict().get('roomId') in rooms]
def photo_urls(n):
 rows=[n.get('photoUrl')]+[v if isinstance(v,str) else v.get('url') for v in n.get('photos',[]) or n.get('photoUrls',[]) or []]+[v.get('url') for v in (n.get('attachments') or []) if v.get('type')=='image']
 return list(dict.fromkeys(v for v in rows if isinstance(v,str) and v.startswith('https://')))
changes=[];identities={};general_plan=None
for n in notes:
 d=n.to_dict();text=d.get('text','');role='facade' if text.startswith('Storefront') or n.id=='QcpfslsNruIAEQoP5HNT' else 'map' if text.startswith('Location map') else None
 if not role:continue
 urls=photo_urls(d)
 if len(urls)!=1:raise SystemExit('Expected a single identification photo')
 rid=d['roomId'];field='facadePhoto' if role=='facade' else 'locationMap';value={'url':urls[0],'sourceNoteId':n.id,'role':role}
 previous=rooms[rid].to_dict().get(field)
 if previous and previous.get('url')!=urls[0]:raise SystemExit('Existing identification differs; review before replacing')
 identities.setdefault(rid,{})[field]=value;changes.append((n.reference,{'reportRole':role}))
 if role=='map' and rooms[rid].to_dict().get('name')=='Common Area':general_plan={**value,'kind':'site-plan'}
if sum('facadePhoto' in v for v in identities.values())!=10:raise SystemExit('Expected ten storefront identifications')
if not general_plan:raise SystemExit('General location plan missing')
if p.to_dict().get('reportCover') and p.to_dict()['reportCover'].get('url')!=general_plan['url']:raise SystemExit('Existing project cover differs')
batch=db.batch()
for ref,data in changes:batch.update(ref,data)
for rid,data in identities.items():batch.update(rooms[rid].reference,data)
batch.update(p.reference,{'reportCover':general_plan});batch.commit()
for rid,data in identities.items():
 saved=rooms[rid].reference.get().to_dict()
 if any(saved.get(k)!=v for k,v in data.items()):raise SystemExit('Saved identity verification failed')
print('ARLINGTON_IDENTITY_VERIFIED',len(identities),'units; 10 storefronts; notes and task states preserved')
