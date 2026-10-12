"""Apply the user-authorized October 12 plan; preserve existing work status."""
import os,json,hashlib
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
uid='zGxpaT3jW5S860Z49dma1FjINVJ2';pid='o3igcYUWRFxNTXRb9kbx';day='2026-10-12'
userref=db.collection('users').document(uid);pref=db.collection('projects').document(pid)
plans=[
 ('1dqeO5qYhH6E2cNWsdjN','4d7zKxI1UWyDQPsARur9','Install new panel-to-rooftop HVAC supply cable for store 06','Morning','Morning plan for October 12: continue the condenser supply-cable work. Find the routes from the junction box in the crawl space to the panels of the two stores, coordinate store access, drill the necessary openings and pull the cables to the panels. Store 06 is 7 Star Grocery / Seven Grocers; the second store name remains to be confirmed. This is planned work; completion has not been reported.'),
 ('ckEowyi2AG348SXPxMq2','PiSH7D4GjeCtRcAtjyDi','Coax Cable Routing','Afternoon','Afternoon plan for October 12: continue the Arlington internet/coax cable installation, following the existing store tasks and actual remaining work. No additional store priority or exact start time was specified. This is planned work; completion has not been reported.')
]
refs=[db.collection('tasks').document(x[0]) for x in plans]
roomrefs=[db.collection('rooms').document(x[1]) for x in plans]
backup={}
entry={'id':'tiago-arlington-20261012','uid':uid,'startDate':day,'endDate':day,'weekends':False,'startTime':'','address':'455 Massachusetts Ave, Arlington, MA','note':'Morning: condenser supply cables from the crawl-space junction box to the panels of two stores; second store identity pending confirmation. Afternoon: continue internet/coax cabling.','cancelled':False}
marker='[October 12, 2026 schedule]'
@firestore.transactional
def apply(tx):
 user=userref.get(transaction=tx).to_dict();project=pref.get(transaction=tx).to_dict()
 snaps=[r.get(transaction=tx) for r in refs];rooms=[r.get(transaction=tx) for r in roomrefs]
 assert user and user.get('name')=='tiagoeliasusa' and user.get('active') is not False and user.get('status')!='inactive'
 assert project and 'arlington' in project.get('name','').lower()
 previous=project.get('employeeSchedule') or [];assert isinstance(previous,list)
 existing=[e for e in previous if e.get('id')==entry['id']]
 assert not existing or existing==[entry],'Existing allocation differs; review before changing'
 backup['project']={'id':pid,'employeeSchedulePresent':'employeeSchedule' in project,'employeeSchedule':project.get('employeeSchedule')}
 backup['tasks']=[]
 for ref,snap,room,plan in zip(refs,snaps,rooms,plans):
  data=snap.to_dict();rdata=room.to_dict()
  assert data and rdata and rdata.get('projectId')==pid
  assert data.get('projectId')==pid and data.get('roomId')==plan[1] and data.get('name')==plan[2] and not data.get('done')
  assert data.get('assignedTo') in [None,'',uid] and data.get('assignedDate') in [None,'',day],'Existing assignment differs; stopped'
  description=data.get('description') or ''
  if marker in description:
   assert plan[4] in description,'Previously added instructions differ'
  else:description=(description+'\n\n'+marker+'\n'+plan[4]).strip()
  backup['tasks'].append({'id':ref.id,'data':data})
  plan_changes={'assignedTo':uid,'assignedDate':day,'plannedTime':data.get('plannedTime') or None,'description':description}
  tx.update(ref,plan_changes)
 if not existing:tx.update(pref,{'employeeSchedule':previous+[entry]})
apply(db.transaction())
after=pref.get().to_dict();assert entry in after['employeeSchedule']
allowed={'assignedTo','assignedDate','plannedTime','description'}
for before,ref,plan in zip(backup['tasks'],refs,plans):
 after_task=ref.get().to_dict()
 assert after_task['assignedTo']==uid and after_task['assignedDate']==day and not after_task['done'] and plan[4] in after_task['description']
 assert {k:v for k,v in before['data'].items() if k not in allowed}=={k:v for k,v in after_task.items() if k not in allowed},'Unrelated task data changed'
assert [e for e in after['employeeSchedule'] if e.get('id')!=entry['id']]==[e for e in (backup['project']['employeeSchedule'] or []) if e.get('id')!=entry['id']]
out=Path('schedule-verification');out.mkdir(exist_ok=True)
(out/'before.json').write_text(json.dumps(backup,indent=2,default=str))
result={'user':'tiagoeliasusa','uid':uid,'date':day,'project':'COAX Main · Arlington','allocationSaved':True,'tasksSaved':[{'id':p[0],'period':p[3],'name':p[2]} for p in plans],'completionStatusPreserved':True,'secondStoreIdentity':'pending confirmation','exactTimes':'not specified'}
(out/'verified.json').write_text(json.dumps(result,indent=2))
print('SCHEDULE_PERSISTENCE_VERIFIED',json.dumps(result),flush=True)
