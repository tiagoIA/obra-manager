import os,json
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
pid='o3igcYUWRFxNTXRb9kbx'
project=db.collection('projects').document(pid).get()
assert project.exists and 'arlington' in project.to_dict()['name'].lower()
rooms=[d for d in db.collection('rooms').where('projectId','==',pid).stream() if d.to_dict().get('name','').strip().lower()=='roof']
assert len(rooms)==1
room=rooms[0]
before='HVAC units are already installed on the roof. The equipment supply circuits and the circuit for two outlets have already been brought to the roof.'
scope='Check the existing rooftop circuits. Install 60 A disconnects and connect them to the HVAC units using liquidtight connections. Install two outlets on the existing circuit. Test the completed work and add final photos.'
obs=''
batch=db.batch()
batch.update(room.reference,{'scopeBrief.before':before,'scopeBrief.workScope':scope,'scopeBrief.observations':obs,'scopeBrief.updatedAt':firestore.SERVER_TIMESTAMP,'updatedAt':firestore.SERVER_TIMESTAMP})
note=db.collection('roomNotes').document('arlington-roof-scope-20261009')
snap=note.get()
if snap.exists:
 assert snap.to_dict().get('roomId')==room.id
 batch.update(note,{'text':'BEFORE INSTALLATION — INITIAL CONDITIONS\n'+before+'\n\nWORK SCOPE\n'+scope})
names={
'arlington-roof-20261009-1':'Check existing rooftop circuits',
'arlington-roof-20261009-2':'Check existing HVAC connections',
'arlington-roof-20261009-3':'Install and connect 60 A HVAC disconnects',
'arlington-roof-20261009-4':'Connect disconnects to HVAC units with liquidtight',
}
changed=[]
for tid,name in names.items():
 ref=db.collection('tasks').document(tid)
 t=ref.get()
 if t.exists:
  assert t.to_dict().get('roomId')==room.id and t.to_dict().get('sourceImport')=='arlington-roof-20261009'
  batch.update(ref,{'name':name,'note':''})
  changed.append(tid)
batch.commit()
saved=room.reference.get().to_dict()['scopeBrief']
assert saved['before']==before and saved['workScope']==scope and saved['observations']==''
if snap.exists:assert note.get().to_dict()['text']=='BEFORE INSTALLATION — INITIAL CONDITIONS\n'+before+'\n\nWORK SCOPE\n'+scope
for tid in changed:
 t=db.collection('tasks').document(tid).get().to_dict()
 assert t['name']==names[tid] and t['note']==''
print('ROOF_SIMPLIFIED_VERIFIED',json.dumps({'roomId':room.id,'disconnectAmps':60,'technicalTextRemoved':True,'tasksSimplified':len(changed)}))
