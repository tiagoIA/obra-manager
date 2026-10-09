import gzip, hashlib, json, os, time
from pathlib import Path
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

PROJECT = "obra-manager-4ecc7"
SITE = "sites/" + PROJECT
CHANNEL = "home-photos-20261009"
API = "https://firebasehosting.googleapis.com/v1beta1/"
key = json.loads(os.environ["FIREBASE_SA"])
if key.get("project_id") != PROJECT:
    raise SystemExit("Unexpected Firebase project")
session = AuthorizedSession(service_account.Credentials.from_service_account_info(
    key, scopes=["https://www.googleapis.com/auth/cloud-platform"]))

def call(method, path, **kwargs):
    response = session.request(method, API + path, timeout=60, **kwargs)
    if not response.ok:
        error = response.json().get("error", {})
        raise SystemExit(f"{method} {path}: HTTP {response.status_code}: {error.get('message', '')}")
    return response.json() if response.content else {}

live = call("GET", SITE + "/channels/live")
source = live["release"]["version"]["name"]
baseline = Path('backups/index-2026-10-09.html').read_bytes()
before = requests.get('https://' + PROJECT + '.web.app/', timeout=30)
if not before.ok or before.content != baseline:
    raise SystemExit('Live HTML changed since backup; publication stopped to preserve newer edits')
Path("hosting-test").mkdir(exist_ok=True)
Path("hosting-test/live-before.json").write_text(json.dumps(live, indent=2))
operation = call("POST", SITE + "/versions:clone", json={"sourceVersion": source, "finalize": False})
for _ in range(60):
    if operation.get("done"):
        break
    time.sleep(2)
    operation = call("GET", operation["name"])
else:
    raise SystemExit("Clone timed out")
if operation.get("error"):
    raise SystemExit("Clone failed: " + json.dumps(operation["error"]))
version = operation["response"]["name"]
if not version.startswith(SITE + "/versions/"):
    raise SystemExit("Unexpected clone version")
marker = Path('public/index.html').read_bytes()
compressed = gzip.compress(marker, mtime=0)
digest = hashlib.sha256(compressed).hexdigest()
files = call("POST", version + ":populateFiles", json={"files": {"/index.html": digest}})
if digest in files.get("uploadRequiredHashes", []):
    response = session.post(files["uploadUrl"] + "/" + digest, data=compressed,
                            headers={"Content-Type": "application/octet-stream"}, timeout=60)
    if not response.ok:
        raise SystemExit(f"File upload failed: HTTP {response.status_code}")
call("PATCH", version, params={"updateMask": "status"}, json={"status": "FINALIZED"})
channel_response = session.get(API + SITE + "/channels/" + CHANNEL, timeout=30)
if channel_response.status_code == 404:
    channel = call("POST", SITE + "/channels", params={"channelId": CHANNEL}, json={"ttl": "604800s"})
elif channel_response.ok:
    channel = channel_response.json()
else:
    raise SystemExit(f"Channel read failed: HTTP {channel_response.status_code}")
release = call("POST", SITE + "/channels/" + CHANNEL + "/releases",
               params={"versionName": version}, json={"message": "Verify Home and photo fixes before live release"})
url = channel["url"]
for attempt in range(12):
    response = requests.get(url + "/", timeout=30,
                            params={"check": os.environ.get("GITHUB_RUN_ID", "test")})
    if response.ok and response.content == marker:
        break
    time.sleep(5)
else:
    raise SystemExit("Published marker verification failed")
after = call("GET", SITE + "/channels/live")
if after["release"]["name"] != live["release"]["name"]:
    raise SystemExit("Live release changed during test; publication stopped")
live_release = call('POST', SITE + '/releases', params={'versionName': version},
                    json={'message': 'User-authorized Home selection, recent projects, photo zoom and uncropped reports'})
live_url = 'https://' + PROJECT + '.web.app/'
for attempt in range(12):
    response = requests.get(live_url, timeout=30, params={'check': os.environ.get('GITHUB_RUN_ID', 'test')})
    if response.ok and response.content == marker:
        break
    time.sleep(5)
else:
    raise SystemExit('Live release created, but HTTP verification failed; inspect result before retrying')
result = {"preview_url": url, "live_url": live_url,
          "version": version, "release": release["name"],
          "previous_live_version": source, "live_release": live_release['name'],
          "live_html_verified": True}
Path("hosting-test/result.json").write_text(json.dumps(result, indent=2))
print("PUBLICATION_VERIFIED", json.dumps(result))
