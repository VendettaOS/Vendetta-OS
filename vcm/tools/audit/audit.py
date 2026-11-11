import uuid
from datetime import datetime, timezone
from vcm.storage import append_jsonl, read_jsonl

def utc_now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def record(case_folder, action, actor, result="success", object_id=None, details=None, durable=False):
    event = {"schema_version":1, "event_id":f"EVT-{uuid.uuid4()}", "timestamp_utc":utc_now(), "case_id":case_folder.name, "action":action, "actor":actor, "result":result}
    if object_id: event["object_id"] = object_id
    if details: event["details"] = details
    append_jsonl(case_folder / "logs" / "audit.jsonl", event, durable)
    return event
def events(case_folder): return read_jsonl(case_folder / "logs" / "audit.jsonl")
