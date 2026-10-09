# Read-only production checks; no sample evidence or fabricated observations are inserted.
import json,os,urllib.request
from google.cloud import firestore
from google.oauth2 import service_account
from pathlib import Path
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
room=db.collection('rooms').document('4d7zKxI1UWyDQPsARur9').get();assert room.exists
r=room.to_dict();assert r['name']=='Roof';assert r['projectId']=='o3igcYUWRFxNTXRb9kbx'
b=r.get('scopeBrief',{});notes=list(db.collection('roomNotes').where('roomId','==',room.id).stream());urls=[]
if r.get('photos',{}).get('before'):urls.append(r['photos']['before'])
urls += [p if isinstance(p,str) else p['url'] for p in b.get('photos',[])]
for n in notes:
 data=n.to_dict()
 if data.get('phase')=='before-installation':
  if data.get('photoUrl'):urls.append(data['photoUrl'])
  urls += [p if isinstance(p,str) else p['url'] for p in data.get('photoUrls',[])]
urls=list(dict.fromkeys(urls));loadable=0
for url in urls:
 with urllib.request.urlopen(url,timeout=30) as response:
  assert response.status==200 and response.headers.get('Content-Type','').startswith('image/')
  loadable+=1
scope=b.get('workScope','');assert '60' in scope,'Review Roof disconnect scope: missing 60 A'
report={'unit':'Roof','scope':scope,'beforePhotos':len(urls),'loadablePhotos':loadable,'existingFieldRecords':len(notes),'readOnly':True}
Path('hosting-test').mkdir(exist_ok=True);Path('hosting-test/roof-evidence-audit.json').write_text(json.dumps(report,indent=2))
print('ROOF_EVIDENCE_VERIFIED',json.dumps(report),flush=True)
