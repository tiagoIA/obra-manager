"""Apply Tiago's reported October 9 progress once, preserving original records and links."""
import copy, json, os, urllib.request
from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account
from initialize_report_summary import SUMMARY
ROOM = '4d7zKxI1UWyDQPsARur9'
PROJECT_ID = 'o3igcYUWRFxNTXRb9kbx'
NOTE_ID = '52863fba-ec33-4c73-b10c-2c73089d4c54'
NOTE_TEXT = "WORK SEQUENCE — October 9, 2026\n\nMorning — material preparation: after reviewing the work and material needs, two disconnects and two outlets with outdoor covers were purchased. Pedro also went to storage to collect materials.\n\nCable identification and investigation: after the purchase, installation began with identifying the existing cables. The investigation found problems with the existing supply cables; the team concluded that new panel-to-rooftop feed cables are required.\n\nPartial installation after investigation: the disconnects were mounted and the LOAD-side connections from the disconnects to the HVAC equipment were installed. The LINE/feed connections from the panel remain pending. The six attached photos document this stage.\n\nRemaining work: run and connect the new feed from the panel to the disconnects; identify and check the existing rooftop cables for the two outlets before installing the outlets and outdoor covers; complete final checks. No completed panel feed or successful final test is recorded."
UPDATES = json.loads("{\"followUp.status\":\"Disconnects mounted and LOAD-side connections to the HVAC equipment installed. New panel feed, outlet-cable verification and final checks remain pending.\",\"followUp.reportSummary.workDone\":\"Morning: materials were reviewed; two disconnects and two outlets with outdoor covers were purchased, and Pedro collected materials from storage. Installation then began with cable identification and investigation. Afterwards, the disconnects were mounted and their LOAD-side connections to the HVAC equipment were installed.\",\"followUp.reportSummary.findings\":\"The cable investigation began after the material purchase. The team concluded that new panel-to-rooftop feed cables are required. The LOAD-side connections were advanced separately; the source panel/circuit and the conditions of the outlet cables still need verification.\",\"followUp.reportSummary.pending\":\"Run and connect the new panel feed to the disconnects; identify and verify the existing rooftop cables for the two outlets; install the outlets and outdoor covers after verification; complete final checks. Cable specifications, route length and the serving panel/circuit remain to be confirmed.\",\"followUp.reportSummary.workScope\":\"Complete the new panel-to-rooftop feed and LINE-side connections to the installed disconnects. Verify the existing outlet cables, install the two outlets with outdoor covers and perform final checks. The disconnect mounting and LOAD-side connections are recorded as completed.\",\"followUp.nextStep\":\"1. Confirm the serving panel/circuit, cable specification and route length.\\n2. Run and connect the new panel feed to the disconnect LINE terminals.\\n3. Identify and check the existing rooftop cables for the two outlets.\\n4. Install the two outlets and outdoor covers after cable verification.\\n5. Complete final checks and record the results.\"}")
OLD_STATUS = 'Investigation completed; new panel-to-rooftop supply cable required; installation pending return.'
OLD_NEXT = "1. Coordinate with store 06 to have the basement hatch and access route cleared before the return visit.\n2. Confirm the serving panel, available circuit, HVAC-unit identity, conductor sizing and cable route/length.\n3. Prepare and review the purchase list once these measurements/specifications are confirmed.\n4. Return to install the new supply cable from the panel to the rooftop HVAC unit, complete the disconnect/liquidtight connections, and perform the required checks and final documentation.\n5. Confirm separately the status of the other rooftop unit and the two outlet circuits."
def main():
    key=json.loads(os.environ['FIREBASE_SA']); assert key['project_id']=='obra-manager-4ecc7'
    db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
    ref=db.collection('rooms').document(ROOM)
    note_ref=db.collection('roomNotes').document(NOTE_ID)
    operation=db.collection('maintenanceOperations').document('roof-oct9-load-progress-v1')
    if operation.get().exists:
        print('ROOF_PROGRESS_ALREADY_RECORDED — no data overwritten',flush=True); return
    room=ref.get().to_dict(); assert room and room['projectId']==PROJECT_ID and room['name']=='Roof'
    note=note_ref.get().to_dict()
    assert note and note['roomId']==ROOM and note['projectId']==PROJECT_ID and note['text']==NOTE_TEXT
    assert note['phase']=='during-work'
    urls=set()
    if note.get('photoUrl'): urls.add(note['photoUrl'])
    for field in ['photos','photoUrls','attachments']:
        for row in note.get(field,[]):
            url=row if isinstance(row,str) else row.get('url')
            if url: urls.add(url)
    assert len(urls)==6, 'Require all six supplied photos before updating the summary'
    for url in urls:
        with urllib.request.urlopen(url,timeout=30) as response:
            assert response.status==200 and response.headers.get('Content-Type','').startswith('image/')
    old=room['followUp']
    assert old.get('reportSummary')==SUMMARY and old.get('status')==OLD_STATUS and old.get('nextStep')==OLD_NEXT, 'Follow-up changed since review; stop without overwriting newer work'
    notes={n.id:n.to_dict() for n in db.collection('roomNotes').where('roomId','==',ROOM).stream()}
    tasks={t.id:t.to_dict() for t in db.collection('tasks').where('roomId','==',ROOM).stream()}
    patch=copy.deepcopy(UPDATES)
    history=copy.deepcopy(old.get('history',[]))
    history.append({'at':datetime.now(timezone.utc).isoformat(),'by':'maintenance-service','reportedBy':'Tiago','sourceNoteId':NOTE_ID,'workDate':'2026-10-09','status':UPDATES['followUp.status'],'nextStep':UPDATES['followUp.nextStep'],'reportSummary':{**SUMMARY,**{k.rsplit('.',1)[-1]:v for k,v in UPDATES.items() if k.startswith('followUp.reportSummary.')}}})
    patch['followUp.history']=history
    expected=copy.deepcopy(room)
    for path,value in patch.items():
        target=expected
        pieces=path.split('.')
        for part in pieces[:-1]: target=target[part]
        target[pieces[-1]]=value
    @firestore.transactional
    def update(transaction):
        current=ref.get(transaction=transaction)
        current_note=note_ref.get(transaction=transaction)
        marker=operation.get(transaction=transaction)
        assert not marker.exists and current.to_dict()==room and current_note.to_dict()==note, 'Concurrent edit; progress update stopped'
        transaction.update(ref,patch)
        transaction.create(operation,{'roomId':ROOM,'projectId':PROJECT_ID,'sourceNoteId':NOTE_ID,'workDate':'2026-10-09','recordedAt':datetime.now(timezone.utc).isoformat(),'reportedBy':'Tiago','fields':list(UPDATES)})
    update(db.transaction())
    assert ref.get().to_dict()==expected
    assert notes=={n.id:n.to_dict() for n in db.collection('roomNotes').where('roomId','==',ROOM).stream()}
    assert tasks=={t.id:t.to_dict() for t in db.collection('tasks').where('roomId','==',ROOM).stream()}
    print('ROOF_PROGRESS_VERIFIED — updated reviewed summary; 6 photos load; original notes, tasks, technical references and media links preserved; LINE feed, outlets and final tests pending',flush=True)
if __name__=='__main__': main()
