import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

DATOTE_SIZE: Final = 64 * 1024
DEFAULT_LOG_FILE: Final = Path("evidence_hash_log.jsonl")
HASHES_PERMITIDOS: Final = ("sha256", "sha384", "sha512", "sha3_256", "md5", "sha1")
HASHES_LEGACY: Final = frozenset({"md5", "sha1"})
HASH_LENGTHS: Final = {
    "md5": 32,
    "sha1": 40,
    "sha256": 64,
    "sha384": 96,
    "sha512": 128,
    "sha3_256": 64,
}
EVIDENCE_ROLES: Final = ("original", "working_copy", "derived_result")

EXIT_OK: Final = 0
EXIT_MISMATCH: Final = 1
EXIT_USAGE_ERROR: Final = 2
EXIT_IO_ERROR: Final = 3
EXIT_LOG_ERROR: Final = 4
EXIT_PARTIAL_SUCCESS: Final = 5

TOOL_NAME: Final = "VERIFICADOR DE HASHES"
TOOL_VERSION: Final = "0.3.0-DEMO"
SCHEMA_VERSION: Final = 2


class FileChangedError(OSError):
    """Se lanza cuando un archivo cambia mientras se calcula su hash"""


class LogWriteError(OSError):
    """Se lanza cuando no se puede escribir una entrada en el registro"""


def utc_now() -> str:
    """Devuelve un timestamp ISO 8601 en UTC"""
    return datetime.now(timezone.utc).isoformat()


def warn_legacy_algorithm(algorithm: str) -> None:
    """Advierte si se selecciona un algoritmo con colisiones conocidas por si las dudas"""
    if algorithm in HASHES_LEGACY:
        print(
            f"Advertencia: {algorithm.upper()} es un algoritmo heredado. "
            "Usalo solo por compatibilidad.\n"
            "Para evidencia nueva se recomienda SHA-256.",
            file=sys.stderr,
        )


def normalize_identifier(value: str | None, field_name: str) -> str | None:
    """Limpia un identificador opcional y rechaza valores vacios"""
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} no puede estar vacio.")
    if any(character in normalized for character in "\r\n\t"):
        raise ValueError(f"{field_name} no puede contener saltos de linea ni tabuladores.")
    return normalized


def normalize_expected_hash(expected_hash: str, algorithm: str) -> str:
    """Normaliza y valida la longitud y el formato hexadecimal de un hash"""
    normalized = expected_hash.strip().lower()
    prefix = f"{algorithm}:"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):].strip()

    expected_length = HASH_LENGTHS[algorithm]
    if len(normalized) != expected_length:
        raise ValueError(
            f"Longitud invalida para {algorithm.upper()}: "
            f"se esperaban {expected_length} caracteres y se recibieron {len(normalized)}."
        )
    try:
        bytes.fromhex(normalized)
    except ValueError as exc:
        raise ValueError("El hash esperado debe contener solo caracteres hexadecimales") from exc
    return normalized


def compute_hash(filepath: Path, algorithm: str = "sha256") -> tuple[str, int]:
    """Calcula el hash por bloques y detecta cambios comunes durante la lectura"""
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"Algoritmo no soportado...: {algorithm}") from exc

    try:
        before = filepath.stat()
        if not filepath.is_file():
            raise OSError(f"La ruta no corresponde a un archivo regular...: {filepath}")
        with filepath.open("rb") as file:
            while datote := file.read(DATOTE_SIZE):
                hasher.update(datote)
        after = filepath.stat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Hummm... No se encontro el archivo: {filepath}") from exc
    except PermissionError as exc:
        raise PermissionError(f"Sin permisos para leer...: {filepath}") from exc

    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise FileChangedError(f"El archivo cambio mientras se calculaba su hash: {filepath}")
    return hasher.hexdigest(), after.st_size


def metadata_from_args(args: argparse.Namespace) -> dict[str, str]:
    """Extrae y valida los metadatos forenses opcionales de argparse"""
    values = {
        "case_id": normalize_identifier(args.case_id, "case_id"),
        "evidence_id": normalize_identifier(args.evidence_id, "evidence_id"),
        "operator": normalize_identifier(args.operator, "operator"),
        "evidence_role": args.evidence_role,
        "source": normalize_identifier(args.source, "source"),
    }
    return {key: value for key, value in values.items() if value is not None}


def make_base_entry(
    action: str,
    filepath: Path,
    algorithm: str,
    metadata: dict[str, str] | None = None,
) -> dict:
    """Crea los campos comunes de cada entrada de auditoria"""
    entry = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "action": action,
        "file": str(filepath.absolute()),
        "file_name": filepath.name,
        "algorithm": algorithm,
        "timestamp_utc": utc_now(),
    }
    if metadata:
        entry.update(metadata)
    return entry


def log_entry(entry: dict, log_file: Path, durable: bool = False) -> None:
    """Anade una entrada JSONL"""
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            file.flush()
            if durable:
                os.fsync(file.fileno())
    except OSError as exc:
        raise LogWriteError(f"No se pudo escribir el registro... {log_file}: {exc}") from exc


def cmd_hash(
    filepath: Path,
    algorithm: str,
    log_file: Path,
    metadata: dict[str, str],
    durable_log: bool,
) -> int:
    warn_legacy_algorithm(algorithm)
    digest, size_bytes = compute_hash(filepath, algorithm)
    entry = make_base_entry("hash", filepath, algorithm, metadata)
    entry.update({"digest": digest, "size_bytes": size_bytes, "result": "calculated"})
    log_entry(entry, log_file, durable_log)
    print(f"[{algorithm.upper()}] {filepath} -> {digest}")
    print(f"Registrado en: {log_file}")
    return EXIT_OK


def cmd_verify(
    filepath: Path,
    expected_hash: str,
    algorithm: str,
    log_file: Path,
    metadata: dict[str, str],
    durable_log: bool,
) -> int:
    warn_legacy_algorithm(algorithm)
    normalized_expected = normalize_expected_hash(expected_hash, algorithm)
    digest, size_bytes = compute_hash(filepath, algorithm)
    match = hmac.compare_digest(digest, normalized_expected)
    entry = make_base_entry("verify", filepath, algorithm, metadata)
    entry.update({
        "computed_digest": digest,
        "expected_digest": normalized_expected,
        "size_bytes": size_bytes,
        "match": match,
        "result": "match" if match else "mismatch",
    })
    log_entry(entry, log_file, durable_log)
    if match:
        print("Integridad verificada: el hash calculado coincide con el esperado. (YEEEEI!)")
        print(f"  Hash: {digest}")
        return EXIT_OK
    print("Fallo de integridad: el hash calculado no coincide con el esperado. (Buuuu...)")
    print(f"  Esperado:  {normalized_expected}")
    print(f"  Calculado: {digest}")
    return EXIT_MISMATCH


def cmd_hash_dir(
    dirpath: Path,
    algorithm: str,
    log_file: Path,
    follow_symlinks: bool,
    metadata: dict[str, str],
    durable_log: bool,
) -> int:
    warn_legacy_algorithm(algorithm)
    if not dirpath.is_dir():
        raise NotADirectoryError(f"La ruta no es una carpeta valida...: {dirpath}")

    resolved_log = log_file.absolute()
    files: list[Path] = []
    for path in dirpath.rglob("*"):
        try:
            if not path.is_file():
                continue
            if path.is_symlink() and not follow_symlinks:
                continue
            if path.absolute() == resolved_log:
                continue
            files.append(path)
        except OSError as exc:
            print(f"Advertencia: no se pudo inspeccionar {path}: {exc}", file=sys.stderr)
    files.sort(key=lambda path: str(path).casefold())

    if not files:
        print("No se encontraron archivos para procesar. Parece mi cumpleanos :(")
        return EXIT_OK

    processed = 0
    failed = 0
    for filepath in files:
        try:
            digest, size_bytes = compute_hash(filepath, algorithm)
            entry = make_base_entry("hash", filepath, algorithm, metadata)
            entry.update({"digest": digest, "size_bytes": size_bytes, "result": "calculated"})
            log_entry(entry, log_file, durable_log)
            processed += 1
            print(f"[{algorithm.upper()}] {filepath} -> {digest}")
        except (OSError, ValueError) as exc:
            failed += 1
            print(f"Wupsis... Error con {filepath}: {exc}", file=sys.stderr)

    print(f"\nProcesados correctamente: {processed}")
    print(f"Fallidos: {failed}")
    print(f"Total encontrado: {len(files)}")
    print(f"Registro: {log_file}")
    return EXIT_PARTIAL_SUCCESS if failed else EXIT_OK


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--case-id", help="Identificador estable del caso, por ejemplo VCM-2026-0001")
    parser.add_argument("--evidence-id", help="Identificador estable de la evidencia, por ejemplo EVD-0001")
    parser.add_argument("--operator", help="Persona o cuenta que realiza la operacion")
    parser.add_argument("--evidence-role", choices=EVIDENCE_ROLES, help="Rol del archivo dentro del caso")
    parser.add_argument("--source", help="Origen declarado de la evidencia")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verificador de integridad de evidencia - VendettaOS")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG_FILE, help=f"Ruta del registro JSONL (predeterminado: {DEFAULT_LOG_FILE})")
    parser.add_argument("--durable-log", action="store_true", help="solicitar escritura durable del registro mediante fsync")
    parser.add_argument("--version", action="version", version=f"%(prog)s {TOOL_VERSION}")
    add_common_options(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)
    hash_parser = subparsers.add_parser("hash", help="Calcular y registrar el hash de un archivo")
    hash_parser.add_argument("file", type=Path)
    hash_parser.add_argument("--algorithm", "--hashito", dest="algorithm", default="sha256", choices=HASHES_PERMITIDOS)

    verify_parser = subparsers.add_parser("verify", help="Verificar un archivo contra un hash esperado")
    verify_parser.add_argument("file", type=Path)
    verify_parser.add_argument("expected_hash")
    verify_parser.add_argument("--algorithm", "--hashito", dest="algorithm", default="sha256", choices=HASHES_PERMITIDOS)

    dir_parser = subparsers.add_parser("hash-dir", help="Calcular hashes para los archivos de una carpeta")
    dir_parser.add_argument("dir", type=Path)
    dir_parser.add_argument("--algorithm", "--hashito", dest="algorithm", default="sha256", choices=HASHES_PERMITIDOS)
    dir_parser.add_argument("--follow-symlinks", action="store_true", help="Procesar enlaces simbolicos a archivos")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metadata = metadata_from_args(args)
        if args.command == "hash":
            return cmd_hash(args.file, args.algorithm, args.log, metadata, args.durable_log)
        if args.command == "verify":
            return cmd_verify(args.file, args.expected_hash, args.algorithm, args.log, metadata, args.durable_log)
        if args.command == "hash-dir":
            return cmd_hash_dir(args.dir, args.algorithm, args.log, args.follow_symlinks, metadata, args.durable_log)
    except LogWriteError as exc:
        print(f"Error de registro: {exc}", file=sys.stderr)
        return EXIT_LOG_ERROR
    except (FileNotFoundError, PermissionError, NotADirectoryError, FileChangedError, OSError) as exc:
        print(f"Error de entrada/salida: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    except ValueError as exc:
        print(f"Entrada invalida: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    parser.error("Comando no reconocido...")
    return EXIT_USAGE_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
