"""Initialize only the user-approved Arlington Roof follow-up; preserve all other fields."""
import hashlib,json,os,urllib.request
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
with urllib.request.urlopen('https://obra-manager-4ecc7.web.app/unit-followup.js',timeout=30) as response:
    assert response.read()==Path('public/unit-followup.js').read_bytes(),'Verified follow-up module is not live yet'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
target=db.collection('rooms').document('4d7zKxI1UWyDQPsARur9')
def immutable(data):
    return hashlib.sha256(json.dumps({k:v for k,v in data.items() if k!='followUp'},sort_keys=True,default=str).encode()).hexdigest()
before=target.get().to_dict();assert before['name']=='Roof' and before['projectId']=='o3igcYUWRFxNTXRb9kbx'
task_names={
    'Check existing rooftop circuits',
    'Check existing HVAC connections',
    'Install and connect 60 A HVAC disconnects',
    'Connect disconnects to HVAC units with liquidtight',
    'Install two rooftop outlets on the existing circuit',
    'Test, label and photograph the completed rooftop connections',
    'Install new panel-to-rooftop HVAC supply cable for store 06',
}
tasks=list(db.collection('tasks').where('roomId','==',target.id).stream())
selected=[t for t in tasks if t.to_dict().get('projectId')==before['projectId'] and t.to_dict().get('name') in task_names]
assert {t.to_dict()['name'] for t in selected}==task_names,'Review the existing Roof tasks before linking'
@firestore.transactional
def initialize(tx):
    snap=target.get(transaction=tx);data=snap.to_dict()
    assert data['name']=='Roof' and data['projectId']=='o3igcYUWRFxNTXRb9kbx'
    if data.get('followUp'):
        # Complete the approved links without changing user-entered status, date or responsibility.
        existing=data['followUp'];ids=list(dict.fromkeys([*existing.get('taskIds',[]),*[t.id for t in selected]]))
        preparation={**existing.get('preparation',{})}
        if not preparation.get('materials'):preparation['materials']='no'
        if ids==existing.get('taskIds',[]) and preparation==existing.get('preparation',{}):return False
        for task in selected:
            saved=task.reference.get(transaction=tx)
            assert saved.exists and saved.to_dict().get('roomId')==target.id and saved.to_dict().get('projectId')==data['projectId'] and saved.to_dict().get('name') in task_names,'Linked task changed'
        plan={**existing,'taskIds':ids,'preparation':preparation,'updatedBy':'system:approved-followup-initialization','updatedAt':firestore.SERVER_TIMESTAMP,
              'history':[*existing.get('history',[]),{'by':'system:approved-followup-initialization','at':'2026-10-09','summary':'Linked existing Roof work; materials preparation pending confirmation of cable specification and quantities.'}][-50:]}
        tx.update(target,{'followUp':plan})
        return True
    brief=data.get('scopeBrief',{})
    plan={'status':'Investigation completed; new panel-to-rooftop supply cable required; installation pending return.',
          'nextStep':brief.get('nextStep','').strip() or 'Confirm the cable route and specification, prepare the purchase list, arrange basement access, and schedule a return to install and test the new supply cable.',
          'returnNeeded':'yes','returnDate':'','returnTime':'','responsibleId':'','taskIds':[t.id for t in selected],'listIds':[],
          'preparation':{'access':'no','materials':'no','team':''},
          'accessNote':'Store 06 — Seven Grocers: merchandise was placed over the basement hatch. Coordinate a clear access path before the return visit.',
          'updatedBy':'system:approved-followup-initialization','updatedAt':firestore.SERVER_TIMESTAMP,
          'history':[{'by':'system:approved-followup-initialization','at':'2026-10-09','status':'Investigation completed; return required','nextStep':brief.get('nextStep','')}]} 
    tx.update(target,{'followUp':plan})
    return True
changed=initialize(db.transaction());after=target.get().to_dict();assert immutable(before)==immutable(after),'Fields outside follow-up changed'
assert after.get('followUp'),'Follow-up missing'
report={'unit':'Arlington / Roof','initialized':changed,'otherFieldsUnchanged':True,'status':after['followUp'].get('status'),'returnNeeded':after['followUp'].get('returnNeeded'),'returnDate':after['followUp'].get('returnDate'),'linkedExistingTasks':len(after['followUp'].get('taskIds',[])),'purchaseListCreated':False}
Path('hosting-test').mkdir(exist_ok=True);Path('hosting-test/roof-followup-initialized.json').write_text(json.dumps(report,indent=2))
print('ROOF_FOLLOWUP_VERIFIED',json.dumps(report),flush=True)

