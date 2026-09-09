import argparse as agp
import hashlib as hs
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATOTE_SIZE = 65536 #64KB para que no haga boom en la memoria xd
LOG_FILE = Path("evidence_hash_log.jsonl") #Ruta para los logs... posiblemente ponga una opción para customizar rutas

#Acá se ve por bloques a ver si el hash coincide o nel pastel
def compute_hash(filepath: Path, hashito: str = "sha256") -> str:
    try:
        hasher = hs.new(hashito)
    except ValueError:
        raise ValueError(f"Ijole, eso no lo soportamos: {hashito}")

    try:
        with open(filepath, "rb") as f:
            while DATOTE := f.read(DATOTE_SIZE):
                hasher.update(DATOTE)
    except FileNotFoundError:
        raise FileNotFoundError(f"Encontré a mi papá (nada xd) en: {filepath}")
    except PermissionError:
        raise PermissionError(f"Sin permisos para leer : {filepath}")

    return hasher.hexdigest()
#-----------------------------------------------------------------------------------------------------------------------------

#Agrega una entrada al log de hashes, ojo con el piojo, en formato ---> JSON <---
#Sin querer queriendo me ayudará a pasarlo a C después xd
def log_entry(entry: dict):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_hash(filepath: Path, hashito: str):
    digest = compute_hash(filepath, hashito)
    entry = {
        "action": "hash",
        "file": str(filepath.resolve()),
        "hashito": hashito,
        "hash": digest,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    log_entry(entry)
    print(f"[{hashito.upper()}] {filepath} -> {digest}")
    print(f"Registrado en: {LOG_FILE}")


def cmd_verify(filepath: Path, expected_hash: str, hashito: str):
    digest = compute_hash(filepath, hashito)
    match = digest.lower() == expected_hash.lower()

    entry = {
        "action": "verify",
        "file": str(filepath.resolve()),
        "hashito": hashito,
        "computed_hash": digest,
        "expected_hash": expected_hash,
        "match": match,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    log_entry(entry)

    if match:
        print(f"La evidencia no ha sido alterada (YEEEEI!)")
        print(f"  Hash: {digest}")
    else:
        print(f"Posible alteración, no coincide (Buuuu...)")
        print(f"  Esperado:  {expected_hash}")
        print(f"  Calculado: {digest}")
        sys.exit(1)  # código de salida para hacerlo acá en FA


def cmd_hash_dir(dirpath: Path, hashito: str):
    if not dirpath.is_dir():
        raise NotADirectoryError(f"Verifica que es una carpeta valida... : {dirpath}")

    files = sorted(p for p in dirpath.rglob("*") if p.is_file())
    if not files:
        print("Parece mi cumpleaños (No hay nada xd)")
        return

    for filepath in files:
        try:
            digest = compute_hash(filepath, hashito)
            entry = {
                "action": "hash",
                "file": str(filepath.resolve()),
                "hashito": hashito,
                "hash": digest,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            log_entry(entry)
            print(f"[{hashito.upper()}] {filepath} -> {digest}")
        except (PermissionError, OSError) as e:
            print(f"Wupsis... Error con: {filepath}: {e}")

    print(f"\n{len(files)} Archivo(s) procesados. Registrados en: {LOG_FILE}")


def main():
    parser = agp.ArgumentParser(
        description="Verificador de integridad de evidencia — VendettaOS"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_hash = subparsers.add_parser("hash", help="Calcular y registrar el hash de un archivo")
    p_hash.add_argument("file", type=Path)
    p_hash.add_argument("--hashito", default="sha256", choices=["sha256", "sha1", "md5"])

    p_verify = subparsers.add_parser("verify", help="Verificar un archivo contra un hash esperado")
    p_verify.add_argument("file", type=Path)
    p_verify.add_argument("expected_hash")
    p_verify.add_argument("--hashito", default="sha256", choices=["sha256", "sha1", "md5"])

    p_hashdir = subparsers.add_parser("hash-dir", help="Hashear todos los archivos de una carpeta")
    p_hashdir.add_argument("dir", type=Path)
    p_hashdir.add_argument("--hashito", default="sha256", choices=["sha256", "sha1", "md5"])

    args = parser.parse_args()

    try:
        if args.command == "hash":
            cmd_hash(args.file, args.hashito)
        elif args.command == "verify":
            cmd_verify(args.file, args.expected_hash, args.hashito)
        elif args.command == "hash-dir":
            cmd_hash_dir(args.dir, args.hashito)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()