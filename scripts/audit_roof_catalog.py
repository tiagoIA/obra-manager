import os,json,urllib.request
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
def image_ok(url):
 if not url:return False
 try:
  with urllib.request.urlopen(url,timeout=8) as r:
   return r.status==200 and r.headers.get('Content-Type','').startswith('image/') and bool(r.read(32))
 except Exception:return False
rooms=[s for s in db.collection('rooms').where('projectId','==','o3igcYUWRFxNTXRb9kbx').stream() if s.to_dict().get('name')=='Roof']
assert len(rooms)==1
room=rooms[0].to_dict()
photos=list(room.get('scopeBrief',{}).get('photos',[]))
if room.get('photos',{}).get('before'):photos.append({'url':room['photos']['before']})
for n in db.collection('roomNotes').where('roomId','==',rooms[0].id).stream():
 note=n.to_dict()
 if note.get('phase')=='before-installation' or note.get('notePhase')=='before-installation':
  photos.extend(note.get('photos',[]))
  if note.get('photoUrl'):photos.append({'url':note['photoUrl']})
urls=list(dict.fromkeys(p if isinstance(p,str) else p.get('url') for p in photos))
urls=[u for u in urls if u]
print('ROOF_PHOTOS',json.dumps({'saved':len(urls),'loadable':sum(image_ok(u) for u in urls)}),flush=True)
cache={}
for lid in ['guided-reference-fa-scope-20261009','guided-reference-fa-quote-20261009']:
 snap=db.collection('shoppingLists').document(lid).get()
 assert snap.exists
 data=snap.to_dict();out=[]
 for item in data.get('items',[]):
  mid=item.get('matId')
  if mid and mid not in cache:
   m=db.collection('materials').document(mid).get()
   cache[mid]=m.to_dict() if m.exists else {}
  m=cache.get(mid,{})
  out.append({'name':item.get('name'),'model':m.get('manufacturerPart'),'photo':bool(m.get('photoUrl')),'description':bool(m.get('description')),'suppliers':[s.get('name') for s in m.get('suppliers',[]) if s.get('matchVerified') is not False],'review':m.get('catalogReviewStatus')})
 print('LIST_AUDIT',json.dumps({'name':data.get('name'),'total':len(out),'rows':out}),flush=True)
print('PHOTO_LOAD_AUDIT',json.dumps([{'model':m.get('manufacturerPart'),'loads':image_ok(m.get('photoUrl'))} for m in cache.values() if m.get('photoUrl')]),flush=True)
