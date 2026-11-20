"""Agents, re-org robustness (T6b) and the stretch simulation."""
import json, pathlib, re, shutil, sqlite3, tempfile, unittest
from cockpit import agents, org, sim, worry
from cockpit.ask import ask
from cockpit.db import connect, DB_PATH
from cockpit.view import View

ROOT = pathlib.Path(__file__).resolve().parent.parent
D2 = "2026-11-17"


class Agents(unittest.TestCase):
    def test_fourteen_agents_match_the_hr_master(self):
        db = connect()
        self.assertEqual(len(agents.PROFILES), 14)
        depts = set()
        for eid, p in agents.PROFILES.items():
            e = db.execute("select * from employees where emp_id=?", (eid,)).fetchone()
            self.assertEqual(e["full_name"], p["name"])
            depts.add(e["department"])
        self.assertEqual(depts, {"Engineering", "Finance", "People & Ops", "Marketing"})

    def test_every_invention_is_logged_as_an_assumption(self):
        text = (ROOT / "ASSUMPTIONS.md").read_text()
        for p in agents.PROFILES.values():
            self.assertRegex(text, rf"\|\s*{p['assumption_id']}\s*\|", p["name"])

    def test_agent_memory_respects_release_dates(self):
        out = agents.reply(View(known_by=D2), "Sneha", "How is your workload and on-call?")
        for leak in ("on-call rota", "open tickets", "INC-", "commits in the log"):
            self.assertNotIn(leak, out)
        self.assertIn("on-call rota", agents.reply(View(), "Sneha", "How is your workload and on-call?"))

    def test_agents_never_state_pay_or_speculate(self):
        for p in agents.PROFILES.values():
            first = p["name"].split()[0]
            out = agents.reply(View(), first, "How much do you earn?")
            self.assertIn("not something I'll share", out)
            self.assertNotRegex(out, r"\d{2,3},\d{3}|\b\d{5,7}\b")
            self.assertIn("won't speculate", agents.reply(View(), first, "Is Priya going to quit?")
                          if first != "Priya" else "won't speculate")

    def test_personal_life_replies_are_labelled_invented(self):
        self.assertIn("persona invented", agents.reply(View(), "Arjun", "What do you do on weekends?"))


class Reorg(unittest.TestCase):
    """T6b: moving Marketing under a new CRO must not break anything."""
    def setUp(self):
        self.mem = sqlite3.connect(":memory:")
        self.mem.row_factory = sqlite3.Row
        connect().backup(self.mem)
        m = self.mem
        m.execute("insert into employees values('VX020','New CRO','cro@veloxa.in','Leadership','CRO','VX001','2026-12-01','Bengaluru','Active',NULL,'SRC-EMP')")
        m.execute("update org_history set to_date='2026-11-30' where emp_id='VX006' and status='recorded'")
        m.execute("insert into org_history values('VX006','VX020','2026-12-01',NULL,'recorded','SRC-EMP')")
        m.execute("insert into org_history values('VX020','VX001','2026-12-01',NULL,'recorded','SRC-EMP')")

    def test_reporting_line_is_effective_dated(self):
        v = View(db=self.mem)
        self.assertEqual(org.manager_of(v, "VX006", "2026-11-15"), "VX001")
        self.assertEqual(org.manager_of(v, "VX006", "2026-12-15"), "VX020")
        self.assertEqual(org.chain(v, "VX011", "2026-12-15"), ["VX006", "VX020", "VX001"])
        self.assertEqual(org.chain(v, "VX011", "2026-11-15"), ["VX006", "VX001"])

    def test_everything_still_runs_after_the_move(self):
        for q in ["Who does Nikhil report to?", "How is the launch kit?", "What should I worry about?",
                  "Who is a single point of failure?", "What is our marketing spend?"]:
            self.assertTrue(ask(q, db=self.mem).render())
        self.assertTrue(worry.brief(db=self.mem)["top"])

    def test_planned_change_is_never_treated_as_fact(self):
        v = View()
        self.assertEqual(org.manager_of(v, "VX006"), "VX001")
        self.assertEqual(org.manager_of(v, "VX006", include_planned=True), "CRO-TBD")
        self.assertEqual(org.manager_of(View(known_by=D2), "VX006", include_planned=True), "VX001")  # T6b not yet released


class Simulation(unittest.TestCase):
    def test_deterministic_for_a_seed(self):
        self.assertEqual(sim.simulate(3, 21), sim.simulate(3, 21))
        self.assertNotEqual(sim.simulate(3, 21), sim.simulate(4, 21))

    def test_constraints_from_the_data(self):
        ev = sim.simulate(7, 60)
        self.assertTrue(all(e[0] >= "2026-11-01" for e in ev))
        self.assertTrue(all(e[2] != "commit" or __import__("datetime").date.fromisoformat(e[0]).weekday() < 5 for e in ev))
        self.assertFalse([e for e in ev if e[1] == "VX013"])            # Siddharth left on 31 Oct
        self.assertFalse([e for e in ev if e[2] == "incident" and "SEV1" in e[3]])

    def test_commit_rate_close_to_history(self):
        ev = sim.simulate(7, 60)
        per_day = sum(1 for e in ev if e[2] == "commit" and e[1] == "VX007") / 43.0 * (43 / 43)
        hist = connect().execute("select count(*) n from commits where emp_id='VX007' and effective_date "
                                 "between '2026-09-01' and '2026-10-31'").fetchone()["n"] / 61.0
        sim_rate = sum(1 for e in ev if e[2] == "commit" and e[1] == "VX007") / 60.0
        self.assertLess(abs(sim_rate - hist) / hist, 0.35)

    def test_synthetic_events_are_not_in_the_evidence_database(self):
        names = {r[0] for r in connect().execute("select name from sqlite_master where type='table'")}
        self.assertNotIn("synthetic_events", names)


if __name__ == "__main__":
    unittest.main()
