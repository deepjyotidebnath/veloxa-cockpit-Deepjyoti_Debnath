"""CLI.  python -m cockpit brief | ask "question" | agent NAME "question" | simulate | sources | build
Flags: [--known-by DATE] [--as-of DATE] [--all] [--days N] [--seed N]"""
import argparse
from . import ask as askm, worry, db


def main():
    ap = argparse.ArgumentParser(prog="cockpit")
    ap.add_argument("cmd", choices=["brief", "ask", "agent", "agents", "simulate", "sources", "build"])
    ap.add_argument("question", nargs="?")
    ap.add_argument("extra", nargs="?", help="agent: the question to put to the colleague named first")
    ap.add_argument("--known-by", help="only use sources released on/before this date (YYYY-MM-DD)")
    ap.add_argument("--as-of", help="only use facts effective on/before this date")
    ap.add_argument("--all", action="store_true", help="brief: show every ranked item, not just the top three")
    ap.add_argument("--days", type=int, default=14, help="simulate: days after 31 Oct to generate")
    ap.add_argument("--seed", type=int, default=7, help="simulate: random seed (same seed, same output)")
    a = ap.parse_args()
    if a.cmd == "build":
        db.build()
        print("built", db.DB_PATH)
    elif a.cmd == "brief":   # T6a: the default landing view, no question needed
        print(worry.render(worry.brief(a.known_by, a.as_of, top=99 if a.all else 3)))
    elif a.cmd == "ask":
        print(askm.ask(a.question or "", a.known_by, a.as_of).render())
    elif a.cmd == "agents":
        from . import agents
        for p in agents.PROFILES.values():
            print(f"{p['emp_id']}  {p['name']:<22}{p['voice']}")
    elif a.cmd == "agent":
        from . import agents
        from .view import View
        print(agents.reply(View(known_by=a.known_by, as_of=a.as_of), a.question or "", a.extra or "How are you?"))
    elif a.cmd == "simulate":
        from . import sim
        ev = sim.simulate(a.seed, a.days)
        sim.store(ev, a.seed)
        print(f"SYNTHETIC activity 1 Nov onward (seed {a.seed}); stored in build/sim.db, never used as evidence")
        for day, k in sorted(sim.summary(ev).items()):
            print(" ", day, ", ".join(f"{n} {kind}" for kind, n in sorted(k.items())))
    else:
        c = db.connect()
        for r in c.execute("select source_id, kind, released_on, effective_date, reliability, title from sources order by released_on, source_id"):
            print(f"{r['source_id']:<16}{r['kind']:<11}rel {r['released_on']}  eff {str(r['effective_date']):<11}{r['reliability']:<7}{r['title']}")


if __name__ == "__main__":
    main()
