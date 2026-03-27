import os, json, time, requests, firebase_admin
from firebase_admin import credentials, firestore, storage

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyAko6KoBUVhCV-nwhuY15qeJGNzG6BrMfI")
GOOGLE_CX      = os.environ.get("GOOGLE_CX", "41476095691a04598")
STORAGE_BUCKET = "obra-manager-4ecc7.firebasestorage.app"
LIMIT          = int(os.environ.get("LIMIT", "0"))
DELAY          = 1.2

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {"storageBucket": STORAGE_BUCKET})
db  = firestore.client()
bkt = storage.bucket()

def search_image(query):
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query,
              "searchType": "image", "num": 5, "imgSize": "MEDIUM", "safe": "active"}
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
        data = r.json()
        if "items" in data:
            preferred = ["homedepot.com","grainger.com","supplyhouse.com","platt.com","lowes.com"]
            for item in data["items"]:
                if any(p in item.get("link","") for p in preferred):
                    return item["link"]
            return data["items"][0]["link"]
        elif "error" in data:
            print(f"  API error: {data['error'].get('message','')}")
    except Exception as e:
        print(f"  search error: {e}")
    return None

def download_image(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.content) > 3000:
            return r.content
    except Exception as e:
        print(f"  download error: {e}")
    return None

def upload(img_bytes, mat_id):
    try:
        blob = bkt.blob(f"materials/{mat_id}/photo_{int(time.time())}.jpg")
        blob.upload_from_string(img_bytes, content_type="image/jpeg")
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"  upload error: {e}")
    return None

print("=" * 55)
print("OBRA MANAGER — BULK PHOTO UPLOADER")
print("=" * 55)
docs = list(db.collection("materials").stream())
materials = [{"id": d.id, **d.to_dict()} for d in docs if not d.to_dict().get("photoUrl")]
total = len(materials) if LIMIT == 0 else min(LIMIT, len(materials))
print(f"\n{len(materials)} materiais sem foto — processando {total}\n")
ok, fail = [], []
for i, mat in enumerate(materials[:total]):
    name = mat.get("name", "unknown")
    cat  = mat.get("cat", "")
    hint = "electrical" if cat == "eletrica" else "fire alarm" if cat == "fire" else ""
    print(f"[{i+1}/{total}] {name}")
    img_url = search_image(f"{name} {hint} product white background")
    if not img_url:
        print("  nao encontrou"); fail.append(name); time.sleep(DELAY); continue
    img = download_image(img_url)
    if not img:
        print("  falha download"); fail.append(name); time.sleep(DELAY); continue
    pub = upload(img, mat["id"])
    if not pub:
        print("  falha upload"); fail.append(name); time.sleep(DELAY); continue
    db.collection("materials").document(mat["id"]).update({"photoUrl": pub})
    print(f"  salvo!")
    ok.append(name)
    time.sleep(DELAY)
print(f"\nSucesso: {len(ok)} | Falhou: {len(fail)}")
json.dump({"ok": ok, "fail": fail}, open("log.json","w"), ensure_ascii=False, indent=2)
