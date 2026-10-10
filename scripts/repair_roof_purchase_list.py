"""Repair only Tiago's six pending Roof purchasing rows; keep product identity unconfirmed."""
import copy,hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from google.cloud import firestore
from google.oauth2 import service_account
PID='o3igcYUWRFxNTXRb9kbx'
ROOM='4d7zKxI1UWyDQPsARur9'
NAME='Roof — Panel feed materials'
PLANS={
 '4x4 metal box':(2,'un',None,'roof-metal-box.jpg','Visual reference: 4×4 steel box. Confirm depth and knockouts; pictured model is not specified for this order.','Confirm box depth and knockouts.'),
 '4x4 box cover':(2,'un','ELEC-019',None,'Visual reference: 4-inch square cover. Confirm cover style; pictured model is not specified for this order.','Confirm cover style for the 4×4 boxes.'),
 'MC connector':(4,'un',None,'roof-mc-connector.jpg','Visual reference: MC cable connector. Confirm fitting size/type and cable compatibility; pictured model is not specified for this order.','Confirm fitting size/type for the MC cable.'),
 'Breaker 20 A':(1,'un','ELEC-059',None,'Visual reference only: breaker family. Manufacturer, model and pole count remain to be confirmed. Do not order by the pictured model.','20 A. Manufacturer/model and pole count to confirm.'),
 'Breaker 30 A':(1,'un','MAT-40872D668693',None,'Visual reference only: breaker family. Manufacturer, model and pole count remain to be confirmed. Do not order by the pictured model.','30 A. Manufacturer/model and pole count to confirm.'),
 'MC cable 10/2 — ft':(250,'ft','ELEC-082',None,'Visual reference: MC cable family. Requested: 10/2, 250 ft. Confirm exact cable specification.','10/2 MC cable — 250 ft. Confirm exact cable specification.')
}
def main():
 key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
 db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
 marker=db.collection('maintenanceOperations').document('roof-purchasing-photos-job-v1')
 if marker.get().exists:
  print('ROOF_PURCHASING_ALREADY_REPAIRED — no records overwritten',flush=True);return
 lists={s.id:s.to_dict() for s in db.collection('shoppingLists').stream()}
 items={s.id:s.to_dict() for s in db.collection('shoppingItems').stream()}
 candidates=[lid for lid,l in lists.items() if l.get('projectId')==PID and l.get('name')==NAME]
 assert len(candidates)==1,'Expected one Roof purchase list'
 lid=candidates[0];oldlist=lists[lid];selected={iid:i for iid,i in items.items() if i.get('listId')==lid}
 assert len(selected)==6 and not oldlist.get('done'),'Purchase list changed'
 assert set(i['name'] for i in selected.values())==set(PLANS),'Material names changed'
 room=db.collection('rooms').document(ROOM).get().to_dict();assert room['projectId']==PID and room['name']=='Roof'
 project=db.collection('projects').document(PID).get().to_dict();assert project['name']=='COAX Main · Arlington'
 mats={s.id:s.to_dict() for s in db.collection('materials').stream()}
 patches={};references={}
 for iid,i in selected.items():
  qty,unit,sku,asset,caption,obs=PLANS[i['name']]
  assert i.get('roomId')==ROOM and i.get('roomName')=='Roof' and not i.get('matId') and not i.get('bought') and not i.get('boughtAt'),'Item identity/status changed'
  assert float(i['qty'])==qty and i['unit']==unit,'Quantities or units changed'
  mid=None
  if sku:
   hits=[mid for mid,m in mats.items() if m.get('sku')==sku]
   assert len(hits)==1,'Reference material missing or ambiguous: '+sku
   mid=hits[0];m=mats[mid];assert m.get('photoUrl','').startswith('https://')
   references[mid]=m
  if asset:
   p=Path('public/purchasing-reference')/asset;expected={'roof-metal-box.jpg':'10c2acd1531ccbcacce65b8a6a483deffbfffdce5e7fcb28f6ad2d97a9734e72','roof-mc-connector.jpg':'4b905a5fb8d9f926ce0020b6547541eef315e454f3095175ee453c3668fa356f'}[asset]
   assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
  patches[iid]={'cat':'eletrica','referenceMaterialId':mid,'referencePhotoUrl':'https://obra-manager-4ecc7.web.app/purchasing-reference/'+asset if asset else None,'photoReferenceNote':caption,'obs':obs}
 listpatch={'jobName':project['name']+' — Roof','note':'Materials for the new panel-to-rooftop feed. All items pending purchase. Photos are visual references; confirm exact models and compatibility before ordering.'}
 tx=db.transaction()
 @firestore.transactional
 def apply(tx):
  mr=marker.get(transaction=tx);lr=db.collection('shoppingLists').document(lid).get(transaction=tx)
  current={iid:db.collection('shoppingItems').document(iid).get(transaction=tx).to_dict() for iid in selected}
  currentrefs={mid:db.collection('materials').document(mid).get(transaction=tx).to_dict() for mid in references}
  if mr.exists:return False
  assert lr.to_dict()==oldlist and current==selected and currentrefs==references,'Concurrent edits detected; stopped'
  tx.update(lr.reference,listpatch)
  for iid,patch in patches.items():tx.update(db.collection('shoppingItems').document(iid),patch)
  tx.create(marker,{'listId':lid,'roomId':ROOM,'projectId':PID,'reportedBy':'Tiago','recordedAt':datetime.now(timezone.utc).isoformat(),'beforeList':oldlist,'beforeItems':selected,'patches':patches,'listPatch':listpatch,'reason':'Restore job name and real visual references without selecting unconfirmed product models.'})
  return True
 assert apply(tx),'A concurrent repair occurred; review before publishing'
 afterlists={s.id:s.to_dict() for s in db.collection('shoppingLists').stream()}
 afteritems={s.id:s.to_dict() for s in db.collection('shoppingItems').stream()}
 expectedlists=copy.deepcopy(lists);expectedlists[lid].update(listpatch)
 expecteditems=copy.deepcopy(items)
 for iid,patch in patches.items():expecteditems[iid].update(patch)
 assert afterlists==expectedlists and afteritems==expecteditems,'Unexpected purchasing data change'
 assert db.collection('rooms').document(ROOM).get().to_dict()==room,'Roof changed'
 print('ROOF_PURCHASING_REPAIRED',json.dumps({'listId':lid,'jobName':listpatch['jobName'],'items':6,'pending':6,'photos':6,'quantitiesPreserved':True,'modelsUnconfirmed':True,'otherListsPreserved':True}),flush=True)
if __name__=='__main__':main()
