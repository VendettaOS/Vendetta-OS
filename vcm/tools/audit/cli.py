import argparse, json, sys
from vcm.core.exceptions import VCMError
from vcm.storage import case_path, cases_root
from .audit import events

def main(argv=None):
    parser = argparse.ArgumentParser(description="Consulta independiente de la bitácora VCM")
    parser.add_argument("case_id"); parser.add_argument("--root"); parser.add_argument("--object-id"); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = events(case_path(cases_root(args.root), args.case_id))
        if args.object_id: data = [x for x in data if x.get("object_id") == args.object_id]
        if args.json: print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for x in data: print(f"{x.get('timestamp_utc')} | {x.get('action')} | {x.get('result')} | {x.get('object_id','-')}")
        return 0
    except VCMError as exc: print(f"Error: {exc}", file=sys.stderr); return 3
