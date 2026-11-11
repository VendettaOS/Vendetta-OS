import json
import os
import tempfile
from pathlib import Path
from vcm.core.exceptions import ManifestError

def write_json_atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try: os.unlink(temporary)
        except OSError: pass
        raise

def append_jsonl(path, payload, durable=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        if durable: os.fsync(handle.fileno())

def read_json(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle: data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"No se pudo leer {path}: {exc}") from exc
    if not isinstance(data, dict): raise ManifestError(f"Manifiesto inválido: {path}")
    return data

def read_jsonl(path):
    path = Path(path)
    if not path.exists(): return []
    output = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip(): continue
            try: item = json.loads(line)
            except json.JSONDecodeError as exc: raise ManifestError(f"JSONL inválido en {path}, línea {number}: {exc}") from exc
            if not isinstance(item, dict): raise ManifestError(f"Entrada inválida en {path}, línea {number}")
            output.append(item)
    return output
