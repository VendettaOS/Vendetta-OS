import os
import re
from pathlib import Path
from vcm.core.exceptions import VCMError

CASE_ID_RE = re.compile(r"^VDT-(\d{4})-(\d{4})$")

def cases_root(value=None):
    raw = value or os.environ.get("VCM_CASES_ROOT", "vendetta_cases")
    return Path(raw).expanduser().resolve()

def case_path(root, case_id):
    if not CASE_ID_RE.fullmatch(case_id):
        raise VCMError("ID inválido... Formato esperado: VDT-AAAA-NNNN.")
    return Path(root) / case_id
