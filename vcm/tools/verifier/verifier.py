import hashlib
import hmac
import sys
from pathlib import Path
from vcm.core.exceptions import FileChangedError, VCMError
from vcm.core.models import HashResult

CHUNK_SIZE = 64 * 1024
ALGORITHMS = ("sha256", "sha384", "sha512", "sha3_256", "md5", "sha1")
LEGACY = frozenset({"md5", "sha1"})
LENGTHS = {"md5":32, "sha1":40, "sha256":64, "sha384":96, "sha512":128, "sha3_256":64}

def compute_hash(path, algorithm="sha256"):
    path = Path(path).expanduser().resolve()
    if algorithm not in ALGORITHMS: raise VCMError(f"Algoritmo no soportado: {algorithm}")
    if algorithm in LEGACY: print(f"Advertencia: {algorithm.upper()} es heredado; usa SHA-256 para evidencia nueva.", file=sys.stderr)
    try:
        before = path.stat()
        if not path.is_file(): raise VCMError(f"No es un archivo regular: {path}")
        hasher = hashlib.new(algorithm)
        with path.open("rb") as handle:
            while chunk := handle.read(CHUNK_SIZE): hasher.update(chunk)
        after = path.stat()
    except (FileNotFoundError, PermissionError) as exc: raise VCMError(str(exc)) from exc
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise FileChangedError(f"El archivo cambió durante la lectura: {path}")
    return HashResult(path, algorithm, hasher.hexdigest(), after.st_size)

def normalize_expected(value, algorithm):
    value = value.strip().lower()
    prefix = f"{algorithm}:"
    if value.startswith(prefix): value = value[len(prefix):].strip()
    if len(value) != LENGTHS[algorithm]: raise VCMError(f"Longitud inválida para {algorithm.upper()}.")
    try: bytes.fromhex(value)
    except ValueError as exc: raise VCMError("El hash esperado debe ser hexadecimal.") from exc
    return value

def verify_hash(path, expected, algorithm="sha256"):
    result = compute_hash(path, algorithm)
    expected = normalize_expected(expected, algorithm)
    return result, hmac.compare_digest(result.digest, expected)
