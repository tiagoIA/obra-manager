import os,json
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
pid='o3igcYUWRFxNTXRb9kbx'
p=db.collection('projects').document(pid).get()
assert p.exists and 'arlington' in p.to_dict()['name'].lower()
rooms=[d for d in db.collection('rooms').where('projectId','==',pid).stream() if d.to_dict().get('name','').strip().lower() in ['roof','roof condenser']]
assert len(rooms)<=1,'Multiple rooftop units need review'
rid=rooms[0].id if rooms else 'arlington-roof-20261009'
room=db.collection('rooms').document(rid)
before='HVAC outdoor units are already installed on the roof. Other electricians have already brought the equipment supply circuits and the circuit for two outlets to the roof. Circuit origins, identification, conductor conditions, protection and equipment nameplates still need to be verified before connection. Reference: rooftop video supplied on 2026-10-09.'
scope='Verify the existing circuits from the source panel to the roof; identify and record the panel and breaker for each feed. Check the equipment nameplates and existing wiring. Install and connect the equipment disconnects to the existing rooftop feeds. Connect each disconnect to its corresponding HVAC unit using specified liquidtight conduit/whips and connectors. Install two rooftop outlets on the existing outlet circuit. Complete checks, identification, functional testing and final photos. HVAC units are already installed; installation of units and new panel-to-roof feeds are outside this defined work unless a defect requires a separately documented change.'
obs='Confirm the number of HVAC units and disconnects, nameplate voltage/MCA/MOCP, breaker types/ratings, conductor sizes and routes. Measure each disconnect-to-unit run before ordering liquidtight fittings and conductors. Confirm suitable outdoor enclosures, outlet protection, covers, bonding and mounting. Do not order breaker ratings or conductor sizes from the video alone.'
brief={'before':before,'workScope':scope,'observations':obs,'referenceVideo':'CameraRecording-A801D5D1-84B5-4104-BA0A-A05B61FBB778.mp4','captureStatus':'before-photos-needed','updatedAt':firestore.SERVER_TIMESTAMP}
batch=db.batch()
if rooms:
 old=rooms[0].to_dict()
 if old.get('scopeBrief'):raise SystemExit('Existing roof scope found; inspect before changing')
 batch.update(room,{'name':'Roof','scopeBrief':brief,'updatedAt':firestore.SERVER_TIMESTAMP})
else:batch.create(room,{'name':'Roof','floor':'Exterior','projectId':pid,'scopeBrief':brief,'createdAt':firestore.SERVER_TIMESTAMP})
note=db.collection('roomNotes').document('arlington-roof-scope-20261009')
if not note.get().exists:
 batch.create(note,{'roomId':rid,'projectId':pid,'text':'BEFORE / INITIAL CONDITIONS\n'+before+'\n\nWORK SCOPE\n'+scope+'\n\nOBSERVATIONS / MATERIALS TO CONFIRM\n'+obs,'transcript':None,'audioUrl':None,'photoUrl':None,'savedAt':'2026-10-09','createdAt':firestore.SERVER_TIMESTAMP,'noteType':'scope','sourceImport':'arlington-roof-20261009'})
tasks=[
 ('Verify and identify existing rooftop circuits from the panel','inspecao',0,False),
 ('Record HVAC nameplates and verify wiring / disconnect specifications','inspecao',0,False),
 ('Install and connect HVAC disconnects to existing rooftop feeds','eletrica',0,False),
 ('Connect disconnects to HVAC units with specified liquidtight whips','eletrica',0,False),
 ('Install two rooftop outlets on the existing circuit','eletrica',2,True),
 ('Test, label and photograph the completed rooftop connections','inspecao',0,False)]
existing=list(db.collection('tasks').where('roomId','==',rid).stream())
for n,(name,cat,qty,hasQty) in enumerate(tasks):
 if any(d.to_dict().get('name','').strip().lower()==name.lower() for d in existing):continue
 ref=db.collection('tasks').document('arlington-roof-20261009-'+str(n+1))
 if not ref.get().exists:batch.create(ref,{'projectId':pid,'roomId':rid,'name':name,'cat':cat,'qty':qty,'hasQty':hasQty,'done':False,'doneAt':None,'photos':[],'note':obs if n<4 else '', 'createdAt':firestore.SERVER_TIMESTAMP,'sourceImport':'arlington-roof-20261009'})
batch.commit()
check=room.get().to_dict()
assert check['name']=='Roof' and check['scopeBrief']['workScope']==scope
assert note.get().exists
tasks_now=list(db.collection('tasks').where('roomId','==',rid).stream())
assert all(any(d.to_dict().get('name')==t[0] for d in tasks_now) for t in tasks)
print('ROOF_VERIFIED',json.dumps({'projectId':pid,'projectName':p.to_dict()['name'],'roomId':rid,'name':check['name'],'reusedExistingUnit':bool(rooms),'totalTasks':len(tasks_now),'scopeSaved':True,'noteSaved':True,'photoCapturePending':True}),flush=True)
