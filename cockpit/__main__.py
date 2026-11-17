"""CLI.  python -m cockpit brief | ask "question" | sources   [--known-by DATE] [--as-of DATE] [--all]"""
import argparse
from . import ask as askm, worry, db


def main():
    ap = argparse.ArgumentParser(prog="cockpit")
    ap.add_argument("cmd", choices=["brief", "ask", "sources", "build"])
    ap.add_argument("question", nargs="?")
    ap.add_argument("--known-by", help="only use sources released on/before this date (YYYY-MM-DD)")
    ap.add_argument("--as-of", help="only use facts effective on/before this date")
    ap.add_argument("--all", action="store_true", help="brief: show every ranked item, not just the top three")
    a = ap.parse_args()
    if a.cmd == "build":
        db.build()
        print("built", db.DB_PATH)
    elif a.cmd == "brief":   # T6a: the default landing view, no question needed
        print(worry.render(worry.brief(a.known_by, a.as_of, top=99 if a.all else 3)))
    elif a.cmd == "ask":
        print(askm.ask(a.question or "", a.known_by, a.as_of).render())
    else:
        c = db.connect()
        for r in c.execute("select source_id, kind, released_on, effective_date, reliability, title from sources order by released_on, source_id"):
            print(f"{r['source_id']:<16}{r['kind']:<11}rel {r['released_on']}  eff {str(r['effective_date']):<11}{r['reliability']:<7}{r['title']}")


if __name__ == "__main__":
    main()
