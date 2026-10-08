import json, os, re, sys
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

PROJECT = "obra-manager-4ecc7"
NEW_NAME = "COAX Main · Arlington"
key = json.loads(os.environ["FIREBASE_SA"])
if key.get("project_id") != PROJECT:
    raise SystemExit("Wrong Firebase project; stopped")
session = AuthorizedSession(service_account.Credentials.from_service_account_info(
    key, scopes=["https://www.googleapis.com/auth/cloud-platform"]))
base = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
backup = Path("backup/arlington-project-before.json")

def checked(response):
    if not response.ok:
        raise SystemExit(f"Firebase request failed: HTTP {response.status_code}")
    return response.json()

def is_target(name):
    return re.fullmatch(r"(?:cat\s*6|coax)\s+main\s*[·—-]\s*arlington", name.strip(), re.I) is not None

if sys.argv[1] == "backup":
    matches = []
    token = None
    while True:
        params = {"pageSize": 100}
        if token:
            params["pageToken"] = token
        result = checked(session.get(base + "/projects", params=params, timeout=30))
        for document in result.get("documents", []):
            name = document.get("fields", {}).get("name", {}).get("stringValue", "")
            if is_target(name):
                matches.append(document)
        token = result.get("nextPageToken")
        if not token:
            break
    if len(matches) != 1:
        raise SystemExit(f"Expected one matching Arlington project; found {len(matches)}; no writes")
    document = matches[0]
    backup.parent.mkdir(exist_ok=True)
    backup.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Backup prepared for", document["name"].rsplit("/", 1)[-1])
    print("Previous name:", document["fields"]["name"]["stringValue"])
elif sys.argv[1] == "apply":
    document = json.loads(backup.read_text(encoding="utf-8"))
    url = "https://firestore.googleapis.com/v1/" + document["name"]
    current = checked(session.get(url, timeout=30))
    old_name = document["fields"]["name"]["stringValue"]
    if current.get("updateTime") != document.get("updateTime"):
        raise SystemExit("Project changed since backup; no writes")
    if old_name != NEW_NAME:
        checked(session.patch(url, params={
            "updateMask.fieldPaths": "name",
            "currentDocument.updateTime": document["updateTime"]
        }, json={"fields": {"name": {"stringValue": NEW_NAME}}}, timeout=30))
    verified = checked(session.get(url, timeout=30))
    if verified["fields"]["name"]["stringValue"] != NEW_NAME:
        raise SystemExit("Rename verification failed")
    before_fields = dict(document["fields"])
    after_fields = dict(verified["fields"])
    before_fields.pop("name", None)
    after_fields.pop("name", None)
    if before_fields != after_fields:
        raise SystemExit("Unexpected change to other project fields")
    Path("backup/arlington-project-after.json").write_text(
        json.dumps(verified, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VERIFIED: project name is", NEW_NAME)
    print("All other project fields preserved")
else:
    raise SystemExit("Unknown mode")
