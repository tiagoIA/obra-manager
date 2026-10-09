import json,os,re
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ["FIREBASE_SA"])
assert key["project_id"]=="obra-manager-4ecc7"
db=firestore.Client(project=key["project_id"],credentials=service_account.Credentials.from_service_account_info(key))
pattern=re.compile(r"sm[i]?100|sm[i]?co.?210|hwl|hcwl|low frequency|single.gang.*blank|blank.*plate|homeline|pc2r|srled|p2r|sgrk|lens.?r3|sd365|bg.?12lx|ann.?80|es.?50x|mdf.?300|mmf.?300|crf.?300|battery.*7|7.*battery|b300.?16|lock.*breaker|lock.?out|ssm246|backbox|bell",re.I)
mats=[]
for s in db.collection("materials").stream():
 d=s.to_dict()
 if pattern.search(" ".join(str(d.get(k,"")) for k in ["name","sku","manufacturerPart","description"])):
  mats.append({"id":s.id,**{k:d.get(k) for k in ["name","sku","manufacturerPart","cat","unit","active","status"]}})
print("MATCHING_MATERIALS",json.dumps(mats))
users=[{"uid":s.id,"name":s.to_dict().get("name"),"role":s.to_dict().get("role")} for s in db.collection("users").stream()]
print("USER_IDENTITIES",json.dumps(users))
temps=[{"id":s.id,"name":s.to_dict().get("name"),"ownerUid":s.to_dict().get("ownerUid"),"items":len(s.to_dict().get("items",[]))} for s in db.collection("shoppingLists").where("listType","==","template").stream()]
print("EXISTING_TEMPLATES",json.dumps(temps))
