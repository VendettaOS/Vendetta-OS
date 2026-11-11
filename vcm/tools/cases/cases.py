from datetime import datetime, timezone
from vcm.core.exceptions import VCMError
from vcm.storage import case_path, read_json, write_json_atomic
from vcm.tools.audit import record

STRUCTURE = ("evidence/originals", "evidence/working-copies", "derived", "notes", "findings", "timelines", "reports", "logs", "manifests")
def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def next_id(root):
    year = datetime.now(timezone.utc).year; highest = 0
    if root.exists():
        for p in root.iterdir():
            parts = p.name.split("-")
            if p.is_dir() and len(parts)==3 and parts[0]=="VDT" and parts[1]==str(year) and parts[2].isdigit(): highest=max(highest,int(parts[2]))
    return f"VDT-{year}-{highest+1:04d}"
def create(root, title, operator, description="", case_id=None, durable=False):
    root.mkdir(parents=True, exist_ok=True); case_id = case_id or next_id(root); folder = case_path(root, case_id)
    if folder.exists(): raise VCMError(f"El caso ya existe: {case_id}")
    for item in STRUCTURE: (folder/item).mkdir(parents=True, exist_ok=False)
    stamp=now(); data={"schema_version":1,"case_id":case_id,"title":title.strip(),"description":description.strip(),"status":"open","created_at":stamp,"created_by":operator,"last_opened_at":stamp,"closed_at":None,"archived_at":None}
    if not data["title"]: raise VCMError("El título no puede estar vacío...")
    write_json_atomic(folder/"case.json",data); record(folder,"case.created",operator,object_id=case_id,durable=durable); return data
def load(root, case_id):
    folder=case_path(root,case_id); data=read_json(folder/"case.json")
    if data.get("case_id") != case_id: raise VCMError("El manifiesto no coincide con el caso...")
    return folder,data
def list_cases(root, status=None):
    if not root.exists(): return []
    output=[]
    for folder in sorted(root.iterdir()):
        if (folder/"case.json").exists():
            data=read_json(folder/"case.json")
            if not status or data.get("status")==status: output.append(data)
    return output
def set_status(root,case_id,status,operator,reason="",durable=False):
    folder,data=load(root,case_id); old=data["status"]
    allowed={("open","closed"),("closed","open"),("closed","archived"),("archived","open")}
    if (old,status) not in allowed: raise VCMError(f"Transición no permitida: {old} -> {status}")
    data["status"]=status; stamp=now()
    if status=="closed": data["closed_at"]=stamp
    if status=="archived": data["archived_at"]=stamp
    if status=="open": data["last_opened_at"]=stamp
    write_json_atomic(folder/"case.json",data); record(folder,f"case.{status}",operator,object_id=case_id,details={"previous_status":old,"reason":reason},durable=durable); return data
