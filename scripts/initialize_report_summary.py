"""One-time reviewed migration. Only new report fields are added; originals stay intact."""
import copy, hashlib, json, os
from google.cloud import firestore
from google.oauth2 import service_account

PROJECT = 'obra-manager-4ecc7'
ROOM = '4d7zKxI1UWyDQPsARur9'
PROJECT_ID = 'o3igcYUWRFxNTXRb9kbx'
EXPECTED = '5be6466045dba636999a85917abbc9d979775f473630eb3f3b8fb10b834faccd'
SUMMARY = {
    'initialConditions': 'Rooftop HVAC equipment and existing supply cables were present before this work.',
    'workScope': 'Install the new supply cable for the HVAC unit serving store 06; complete the disconnect/liquidtight connections and final checks. Confirm separately the other rooftop unit and the two outlet circuits.',
    'workDone': 'Investigated the existing rooftop supply cables in the crawlspace and store 06 basement. Attempted continuity testing and inspected junction boxes. Photos and the original investigation video were recorded.',
    'findings': 'The team reported cut existing supply cables and concluded that a new panel-to-rooftop cable is required for the unit serving store 06. The source panel/circuit has not yet been confirmed.',
    'pending': 'Confirm the serving panel/circuit, HVAC-unit identity, cable specification and route length; prepare the purchase list and schedule the return. Cable replacement, connections and final testing remain pending.',
}
EQUIPMENT = [
    {'name': 'HVAC equipment 1', 'model': 'Samsung AJ024BXS4CH/AA', 'supply': '208–230 V · 1 phase · 60 Hz', 'mca': '26.0 A', 'maxProtection': '30.0 A', 'disconnect': '', 'source': 'nameplate'},
    {'name': 'HVAC equipment 2', 'model': '', 'supply': '208/230 V · 1 phase · 60 Hz', 'mca': '18.3 A', 'maxProtection': '20 A', 'disconnect': '', 'source': 'nameplate'},
]

def main():
    key=json.loads(os.environ['FIREBASE_SA'])
    assert key['project_id']==PROJECT
    db=firestore.Client(project=PROJECT,credentials=service_account.Credentials.from_service_account_info(key))
    ref=db.collection('rooms').document(ROOM)
    snap=ref.get(); assert snap.exists
    room=snap.to_dict(); assert room['projectId']==PROJECT_ID and room['name']=='Roof'
    if room.get('followUp',{}).get('reportSchemaVersion')==1:
        print('REPORT_SCHEMA_ALREADY_INITIALIZED — no records changed',flush=True)
        return
    notes=list(db.collection('roomNotes').where('roomId','==',ROOM).stream())
    tasks=list(db.collection('tasks').where('roomId','==',ROOM).stream())
    state={'room':room,'notes':{n.id:n.to_dict() for n in notes},'tasks':{t.id:t.to_dict() for t in tasks}}
    fingerprint=hashlib.sha256(json.dumps(state,sort_keys=True,default=str).encode()).hexdigest()
    assert fingerprint==EXPECTED, 'Roof changed; reviewed migration stopped rather than overwriting newer work'
    assert not room.get('followUp',{}).get('reportSummary') and not room.get('followUp',{}).get('equipment'), 'Existing structured report fields must not be replaced'
    expected=copy.deepcopy(room)
    expected.setdefault('followUp',{}).update(reportSummary=SUMMARY,equipment=EQUIPMENT,reportSchemaVersion=1)
    @firestore.transactional
    def update(transaction):
        current=ref.get(transaction=transaction)
        assert current.to_dict()==room, 'Concurrent Roof edit; migration stopped'
        # Dot-path updates do not replace planning, scope, history, permissions or task/media links.
        transaction.update(ref, {'followUp.reportSummary':SUMMARY, 'followUp.equipment':EQUIPMENT, 'followUp.reportSchemaVersion':1})
    update(db.transaction())
    assert ref.get().to_dict()==expected, 'Review the migrated report fields before continuing publication'
    after_notes={n.id:n.to_dict() for n in db.collection('roomNotes').where('roomId','==',ROOM).stream()}
    after_tasks={t.id:t.to_dict() for t in db.collection('tasks').where('roomId','==',ROOM).stream()}
    assert after_notes==state['notes'] and after_tasks==state['tasks'], 'Field records or tasks changed during initialization'
    print('REPORT_SCHEMA_INITIALIZED — added reviewed summary and nameplate references; original unit fields, notes, tasks and evidence links preserved',flush=True)

if __name__=='__main__': main()
