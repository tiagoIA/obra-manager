"""Reconcile reported Roof activities and existing evidence once; never delete records."""
import copy, hashlib, json, os
from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account
from update_roof_oct9_progress import NOTE_TEXT
ROOM='4d7zKxI1UWyDQPsARur9'
PID='o3igcYUWRFxNTXRb9kbx'
EXPECTED='3fc7ac4ea1124c8357f7f5909031295e7dc08f920913782e3b69c491aaea58fb'
SOURCE='52863fba-ec33-4c73-b10c-2c73089d4c54'
SCOPE='arlington-roof-scope-20261009'
PLATES='aa348dbd-83b1-4003-b40c-cb0a6681e97d'
TRACE='628ac95d-eb35-4bee-81e0-4a802c53818e'
VIDEO='ee9b427d-98fb-4095-888c-7d3772c15822'
DAILY='79b3cb6c-673f-4d94-bdf5-5028298bb732'
TEXTS=json.loads("[[\"Review initial conditions and work scope\",\"Levantamento das condições iniciais e do escopo\"],[\"Purchase disconnects and outlets with outdoor covers\",\"Compra de disconnects e tomadas com tampas externas\"],[\"Collect materials from storage\",\"Retirada de materiais no storage\"],[\"Record HVAC nameplate specifications\",\"Registro das especificações nas placas das máquinas\"],[\"Investigate rooftop supply cables and document findings\",\"Investigação dos cabos de alimentação do teto e registro das constatações\"],[\"Initial rooftop conditions and the intended installation work were reviewed before material preparation.\",\"Foram levantadas as condições iniciais do teto e o trabalho de instalação previsto, antes da preparação dos materiais.\"],[\"Two disconnects and two outlets with outdoor covers were purchased during the morning.\",\"Foram comprados dois disconnects e duas tomadas com tampas para uso externo durante a manhã.\"],[\"Pedro went to storage to collect materials during the morning preparation.\",\"Pedro foi ao storage buscar materiais durante a preparação da manhã.\"],[\"The equipment nameplates were photographed and their supply, MCA and overcurrent-protection values were documented. Circuit identity remains unconfirmed.\",\"As placas das máquinas foram fotografadas e os valores de alimentação, MCA e proteção contra sobrecorrente foram registrados. A identificação dos circuitos permanece pendente.\"],[\"Cable tracing, attempted continuity testing and junction-box inspection were performed. The findings were documented with photos and the original video. The source panel/circuit was not confirmed; the investigation led to the requirement for a new feed.\",\"Foram realizadas investigação do percurso dos cabos, tentativa de teste de continuidade e inspeção de junction boxes. As constatações foram documentadas com fotos e o vídeo original. O painel/circuito de origem não foi confirmado; a investigação levou à necessidade de alimentação nova.\"],[\"The disconnects were mounted. The panel-side LINE feed remains pending.\",\"Os disconnects foram montados. A alimentação do painel pelo lado LINE permanece pendente.\"],[\"The LOAD-side liquidtight connections from the disconnects to the HVAC equipment were installed. This does not record a completed LINE feed or a successful final test.\",\"Foram realizadas as ligações do lado LOAD com liquidtight, dos disconnects até as máquinas. Esta etapa não registra alimentação concluída pelo lado LINE nem aprovação em teste final.\"]]")
def photos(record):
    rows=[]
    for row in record.get('photoUrls',record.get('photos',[])):
        rows.append({'url':row} if isinstance(row,str) else row)
    if record.get('photoUrl'): rows.append({'url':record['photoUrl']})
    return list(dict.fromkeys(row['url'] for row in rows if row.get('url')))
def main():
    key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
    db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
    marker=db.collection('maintenanceOperations').document('roof-oct9-completed-activities-v1')
    if marker.get().exists:
        print('ROOF_ACTIVITIES_ALREADY_RECONCILED — no records overwritten',flush=True);return
    ref=db.collection('rooms').document(ROOM);room=ref.get().to_dict()
    notes={n.id:n.to_dict() for n in db.collection('roomNotes').where('roomId','==',ROOM).stream()}
    tasks={t.id:t.to_dict() for t in db.collection('tasks').where('roomId','==',ROOM).stream()}
    state={'room':room,'notes':notes,'tasks':tasks}
    assert hashlib.sha256(json.dumps(state,sort_keys=True,default=str).encode()).hexdigest()==EXPECTED,'Roof changed since review; reconciliation stopped'
    assert room['projectId']==PID and room['name']=='Roof' and notes[SOURCE]['text']==NOTE_TEXT
    for nid in [SOURCE,SCOPE,PLATES,TRACE,VIDEO,DAILY]: assert notes[nid]['roomId']==ROOM and notes[nid]['projectId']==PID
    source_photos=photos(notes[SOURCE]);assert len(source_photos)==6
    named={p.get('name'):p['url'] for p in notes[SOURCE].get('photoUrls',[]) if isinstance(p,dict)}
    assert 'IMG_1631.jpeg' in named,'Require identified disconnect mounting photo'
    mount_photo=named['IMG_1631.jpeg']
    stamp=datetime.now(timezone.utc)
    additions={}
    definitions=[
      ('review',TEXTS[0][0],'geral',10,TEXTS[5][0],[SCOPE],photos(notes[SCOPE])),
      ('purchase',TEXTS[1][0],'geral',20,TEXTS[6][0],[SOURCE],[]),
      ('storage',TEXTS[2][0],'geral',30,TEXTS[7][0],[SOURCE],[]),
      ('nameplates',TEXTS[3][0],'inspecao',40,TEXTS[8][0],[PLATES],photos(notes[PLATES])),
      ('investigation',TEXTS[4][0],'inspecao',50,TEXTS[9][0],[TRACE,VIDEO,DAILY],list(dict.fromkeys(photos(notes[VIDEO])+photos(notes[DAILY])))),
    ]
    normalized=lambda name:' '.join(name.lower().split())
    for slug,name,cat,order,brief,nids,pics in definitions:
        assert not any(normalized(t['name'])==normalized(name) for t in tasks.values()),'An activity already exists; review rather than duplicate'
        tid='roof-oct9-'+slug
        additions[tid]={'roomId':ROOM,'projectId':PID,'name':name,'cat':cat,'qty':0,'hasQty':False,'done':True,'doneAt':'10/9/2026','workDate':'2026-10-09','photos':pics,'note':brief,'reportBrief':brief,'reportOrder':order,'sourceObservationId':nids[0],'reportEvidenceNoteIds':nids,'sourceFollowUp':ROOM,'createdBy':'maintenance-service','reportedBy':'Tiago','createdAt':stamp,'completionRecordedAt':stamp}
    patches={}
    for name,order,brief,pics in [('Mount disconnects',60,TEXTS[10][0],[mount_photo]),('Connect disconnects to HVAC units with liquidtight',70,TEXTS[11][0],source_photos)]:
        matches=[(tid,t) for tid,t in tasks.items() if t['name']==name and t['projectId']==PID]
        assert len(matches)==1 and not matches[0][1].get('done'),'Existing task changed; stop before overwriting'
        tid,t=matches[0]
        patches[tid]={'done':True,'doneAt':'10/9/2026','workDate':'2026-10-09','photos':list(dict.fromkeys(t.get('photos',[])+pics)),'reportBrief':brief,'reportOrder':order,'sourceObservationId':t.get('sourceObservationId') or SOURCE,'reportEvidenceNoteIds':list(dict.fromkeys(t.get('reportEvidenceNoteIds',[])+[SOURCE])),'reportedBy':'Tiago','completionRecordedAt':stamp}
    completed_ids=list(additions)+list(patches)
    room_patch={'followUp.taskIds':list(dict.fromkeys(room.get('followUp',{}).get('taskIds',[])+completed_ids)),'followUp.history':room.get('followUp',{}).get('history',[])+[{'at':stamp.isoformat(),'by':'maintenance-service','reportedBy':'Tiago','workDate':'2026-10-09','sourceNoteId':SOURCE,'completedTaskIds':completed_ids,'operation':'Reconcile documented completed activities and evidence'}]}
    expected_tasks=copy.deepcopy(tasks)
    expected_tasks.update(additions)
    for tid,patch in patches.items(): expected_tasks[tid].update(patch)
    expected_room=copy.deepcopy(room)
    for path,value in room_patch.items(): expected_room['followUp'][path.split('.')[1]]=value
    @firestore.transactional
    def apply(transaction):
        current_room=ref.get(transaction=transaction).to_dict()
        current_marker=marker.get(transaction=transaction)
        current_notes={n.id:n.to_dict() for n in db.collection('roomNotes').where('roomId','==',ROOM).stream(transaction=transaction)}
        current_tasks={t.id:t.to_dict() for t in db.collection('tasks').where('roomId','==',ROOM).stream(transaction=transaction)}
        new_refs={tid:db.collection('tasks').document(tid) for tid in additions}
        for target in new_refs.values(): assert not target.get(transaction=transaction).exists
        assert not current_marker.exists and current_room==room and current_notes==notes and current_tasks==tasks,'Concurrent edit; reconciliation stopped'
        for tid,record in additions.items(): transaction.create(new_refs[tid],record)
        for tid,patch in patches.items(): transaction.update(db.collection('tasks').document(tid),patch)
        transaction.update(ref,room_patch)
        transaction.create(marker,{'roomId':ROOM,'projectId':PID,'sourceNoteId':SOURCE,'workDate':'2026-10-09','completedTaskIds':completed_ids,'recordedAt':stamp,'reportedBy':'Tiago'})
    apply(db.transaction())
    assert ref.get().to_dict()==expected_room
    assert {n.id:n.to_dict() for n in db.collection('roomNotes').where('roomId','==',ROOM).stream()}==notes
    final_tasks={t.id:t.to_dict() for t in db.collection('tasks').where('roomId','==',ROOM).stream()}
    assert final_tasks==expected_tasks
    assert sum(bool(t.get('done')) for t in final_tasks.values())==7 and len(final_tasks)==16
    for name in ['Identify cable unit','Check existing rooftop circuits','Test, label and photograph the completed rooftop connections','Install new panel-to-rooftop HVAC supply cable for store 06']:
        assert not next(t for t in final_tasks.values() if t['name']==name)['done']
    print('ROOF_ACTIVITIES_VERIFIED — 5 documented activities created, 2 existing tasks completed, 7/16 completed (44%); photos linked to matching tasks; original notes/video, other task fields and technical values preserved; circuit identification, LINE feed and final checks remain pending',flush=True)
if __name__=='__main__': main()
