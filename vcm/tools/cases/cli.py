import argparse, json, sys
from vcm.core.exceptions import VCMError
from vcm.storage import cases_root
from .cases import create, list_cases, load, set_status

def build_parser():
    p=argparse.ArgumentParser(description="Administrador independiente de casos VCM"); p.add_argument("--root"); sub=p.add_subparsers(dest="command",required=True)
    c=sub.add_parser("create"); c.add_argument("--title",required=True); c.add_argument("--description",default=""); c.add_argument("--operator",required=True); c.add_argument("--case-id")
    l=sub.add_parser("list"); l.add_argument("--status",choices=("open","closed","archived"))
    s=sub.add_parser("show"); s.add_argument("case_id")
    for name in ("close","reopen","archive"):
        x=sub.add_parser(name); x.add_argument("case_id"); x.add_argument("--operator",required=True); x.add_argument("--reason",default="")
    return p

def main(argv=None):
    a=build_parser().parse_args(argv); root=cases_root(a.root)
    try:
        if a.command=="create": data=create(root,a.title,a.operator,a.description,a.case_id)
        elif a.command=="list":
            for data in list_cases(root,a.status): print(f"{data['case_id']} | {data['status']} | {data['title']}")
            return 0
        elif a.command=="show": _,data=load(root,a.case_id)
        else: data=set_status(root,a.case_id,{"close":"closed","reopen":"open","archive":"archived"}[a.command],a.operator,a.reason)
        print(json.dumps(data,ensure_ascii=False,indent=2)); return 0
    except VCMError as exc: print(f"Error: {exc}",file=sys.stderr); return 3
