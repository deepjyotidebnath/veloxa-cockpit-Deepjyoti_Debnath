"""Stretch: colleagues keep generating plausible activity after the 31 Oct 2026 export.

Rules (DECISIONS D-13):
  * Synthetic events live in build/sim.db, a SEPARATE file. The cockpit's evidence database never sees them, so
    ask/brief cannot cite an invented event as fact.
  * Rates come from the real record (git log Aug-Oct, incidents Aug-Oct, rota pattern), not from imagination.
  * Hard constraints from the data: nobody acts after their exit date; weekends are quiet (history: 0 weekend commits
    except Priya's few); Priya's late-night pattern is kept; the incident rate follows Aug-Oct, minus August's spike.
  * Deterministic for a given seed.
"""
import datetime as dt
import pathlib
import random
import sqlite3
from . import db as dbm
from .view import View

SIM_DB = dbm.ROOT / "build" / "sim.db"
START = dt.date(2026, 11, 1)
ENGINEERS = {"VX004": "vikram", "VX007": "priya", "VX009": "arjun", "VX012": "sneha", "VX018": "rahul"}


def _rates(v):
    """Commits per working day per engineer over Sep-Oct 2026, and share of late-night commits."""
    out = {}
    for emp in ENGINEERS:
        r = v.db.execute("select count(*) n, sum(ist_hour>=22 or ist_hour<2) late from commits "
                         "where emp_id=? and effective_date between '2026-09-01' and '2026-10-31'", (emp,)).fetchone()
        out[emp] = (r["n"] / 43.0, (r["late"] or 0) / r["n"] if r["n"] else 0)  # 43 weekdays in Sep-Oct
    return out


def simulate(seed=7, days=14, start=START):
    v = View()
    rng = random.Random(seed)
    rates = _rates(v)
    exits = {r["emp_id"]: r["exit_date"] for r in v.db.execute("select emp_id, exit_date from employees")}
    inc_rate = 5 / 61.0   # Sep-Oct incidents (6 of the 11 were Aug); SEV1 rate 0 after August
    events = []
    for i in range(days):
        d = start + dt.timedelta(days=i)
        iso = d.isoformat()
        weekday = d.weekday() < 5
        for emp, name in ENGINEERS.items():
            if exits.get(emp) and exits[emp] < iso:
                continue
            per_day, late = rates[emp]
            n = sum(rng.random() < min(per_day / 2.0, 0.95) for _ in range(2)) if weekday else 0
            for _ in range(n):
                is_late = rng.random() < late
                hour = rng.choice([22, 23, 0, 1]) if is_late else rng.randint(10, 19)
                events.append((iso, emp, "commit", f"{name}: commit at {hour:02d}:{rng.randint(0, 59):02d} IST "
                               f"to {'atlas-engine' if emp == 'VX007' else rng.choice(['atlas-engine', 'planner-web', 'infra', 'atlas-api'])}"))
        if rng.random() < inc_rate:
            sev = rng.choices(["SEV2", "SEV3"], [0.5, 0.5])[0]
            events.append((iso, "VX012", "incident", f"{sev} on routing-api, paged to on-call"))
        if d.weekday() == 0:
            events.append((iso, "VX012", "oncall", "rota rolls over; Sneha is on the rota again (every week so far)"))
    return events


def store(events, seed, path=SIM_DB):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    c = sqlite3.connect(path)
    c.execute("create table synthetic_events(day text, emp_id text, kind text, text text, synthetic int default 1, seed int)")
    c.executemany("insert into synthetic_events(day, emp_id, kind, text, seed) values(?,?,?,?,?)",
                  [(*e, seed) for e in events])
    c.commit()
    return c


def summary(events):
    by = {}
    for day, emp, kind, _ in events:
        by.setdefault(day, {}).setdefault(kind, 0)
        by[day][kind] += 1
    return by
