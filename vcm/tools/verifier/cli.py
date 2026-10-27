import argparse, json, sys
from vcm.core.exceptions import VCMError
from .verifier import ALGORITHMS, compute_hash, verify_hash

def build_parser():
    parser = argparse.ArgumentParser(description="Verificador independiente de VendettaOS")
    sub = parser.add_subparsers(dest="command", required=True)
    hp = sub.add_parser("hash"); hp.add_argument("file"); hp.add_argument("--algorithm", "--hashito", default="sha256", choices=ALGORITHMS); hp.add_argument("--json", action="store_true")
    vp = sub.add_parser("verify"); vp.add_argument("file"); vp.add_argument("expected_hash"); vp.add_argument("--algorithm", "--hashito", default="sha256", choices=ALGORITHMS); vp.add_argument("--json", action="store_true")
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "hash":
            result = compute_hash(args.file, args.algorithm)
            data = result.to_dict() | {"match": None}
            print(json.dumps(data, ensure_ascii=False) if args.json else f"[{result.algorithm.upper()}] {result.path} -> {result.digest}")
            return 0
        result, match = verify_hash(args.file, args.expected_hash, args.algorithm)
        data = result.to_dict() | {"match": match}
        print(json.dumps(data, ensure_ascii=False) if args.json else ("Integridad verificada. (YEEEEI!)" if match else "Fallo de integridad. (Buuuu...)"))
        return 0 if match else 1
    except VCMError as exc:
        print(f"Error: {exc}", file=sys.stderr); return 3
