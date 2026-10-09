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
@firestore.transactional
def initialize(tx):
    snap=target.get(transaction=tx);data=snap.to_dict()
    assert data['name']=='Roof' and data['projectId']=='o3igcYUWRFxNTXRb9kbx'
    if data.get('followUp'):
        return False
    brief=data.get('scopeBrief',{})
    plan={'status':'Investigation completed; new panel-to-rooftop supply cable required; installation pending return.',
          'nextStep':brief.get('nextStep','').strip() or 'Confirm the cable route and specification, prepare the purchase list, arrange basement access, and schedule a return to install and test the new supply cable.',
          'returnNeeded':'yes','returnDate':'','returnTime':'','responsibleId':'','taskIds':[],'listIds':[],
          'preparation':{'access':'no','materials':'','team':''},
          'accessNote':'Store 06 — Seven Grocers: merchandise was placed over the basement hatch. Coordinate a clear access path before the return visit.',
          'updatedBy':'system:approved-followup-initialization','updatedAt':firestore.SERVER_TIMESTAMP,
          'history':[{'by':'system:approved-followup-initialization','at':'2026-10-09','status':'Investigation completed; return required','nextStep':brief.get('nextStep','')}]} 
    tx.update(target,{'followUp':plan})
    return True
changed=initialize(db.transaction());after=target.get().to_dict();assert immutable(before)==immutable(after),'Fields outside follow-up changed'
assert after.get('followUp'),'Follow-up missing'
report={'unit':'Arlington / Roof','initialized':changed,'otherFieldsUnchanged':True,'status':after['followUp'].get('status'),'returnNeeded':after['followUp'].get('returnNeeded'),'returnDate':after['followUp'].get('returnDate'),'purchaseListCreated':False}
Path('hosting-test').mkdir(exist_ok=True);Path('hosting-test/roof-followup-initialized.json').write_text(json.dumps(report,indent=2))
print('ROOF_FOLLOWUP_VERIFIED',json.dumps(report),flush=True)
