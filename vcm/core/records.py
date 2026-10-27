import re
from datetime import datetime, timezone
from vcm.core.exceptions import VCMError

PREFIX_RE = re.compile(r"^[A-Z]{3,5}$")

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def next_record_id(records, prefix, field):
    if not PREFIX_RE.fullmatch(prefix):
        raise VCMError("Prefijo de registro inválido.")
    highest = 0
    marker = prefix + "-"
    for record in records:
        value = str(record.get(field, ""))
        if value.startswith(marker) and value[len(marker):].isdigit():
            highest = max(highest, int(value[len(marker):]))
    return f"{prefix}-{highest + 1:04d}"

def require_text(value, field):
    cleaned = str(value).strip()
    if not cleaned:
        raise VCMError(f"{field} no puede estar vacío.")
    if any(char in cleaned for char in "\r\n\t"):
        raise VCMError(f"{field} no puede contener saltos de línea ni tabuladores.")
    return cleaned
