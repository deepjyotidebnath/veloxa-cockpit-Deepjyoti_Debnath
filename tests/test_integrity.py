"""Data-integrity and safety tests. Each documents a claim made in TRANSCRIPT_NOTES.md / DECISIONS.md."""
import unittest
from cockpit import worry
from cockpit.view import View
from cockpit.ask import ask
from cockpit.db import connect

D1, D2 = "2026-11-16", "2026-11-17"


class Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = connect()

    def q(self, sql, *a):
        return [tuple(r) for r in self.db.execute(sql, a)]

    def test_row_counts(self):
        for t, n in [("employees", 19), ("gl", 28), ("payroll", 56), ("reqs", 6), ("pulse", 24), ("leave", 19)]:
            self.assertEqual(self.q(f"select count(*) from {t}")[0][0], n, t)

    def test_referential(self):
        self.assertEqual(self.q("select count(*) from leave where emp_id not in (select emp_id from employees)")[0][0], 0)
        self.assertEqual(self.q("select count(*) from employees where manager_id is not null and "
                                "manager_id not in (select emp_id from employees)")[0][0], 0)
        self.assertEqual(self.q("select count(*) from payroll where emp_id not in (select emp_id from employees)")[0][0], 0)

    def test_gl_payroll_equals_register_gross(self):
        """Ledger salary line == March register gross (not net). Supports 'register and GL agree'."""
        gross = self.q("select sum(gross_inr) from payroll where month='Mar-2026'")[0][0]
        self.assertEqual({r[0] for r in self.q("select amount_inr from gl where cost_centre='PAYROLL'")}, {gross})

    def test_feb_joiner_not_prorated(self):
        """Rahul joined 3 Feb but was paid for all 28 days: the anomaly behind emails 01-03."""
        d, jd = self.q("select p.days_payable, e.join_date from payroll p join employees e using(emp_id) "
                       "where emp_id='VX018' and month='Feb-2026'")[0]
        self.assertEqual((d, jd), (28, "2026-02-03"))

    def test_pulse_vs_master_engineering_headcount(self):
        """Pulse says 5 engineers in Oct-Dec 2025; master shows 4 joined by then -> possible missing leaver."""
        pulse = self.q("select team_size from pulse where team='Engineering' and quarter='Oct-Dec 2025'")[0][0]
        master = self.q("select count(*) from employees where department='Engineering' and join_date<='2025-12-31'")[0][0]
        self.assertEqual((pulse, master), (5, 4))

    def test_resignation_matches_master_exit_date(self):
        exit_date = self.q("select exit_date from employees where emp_id='VX013'")[0][0]
        self.assertEqual(exit_date, "2026-10-31")
        self.assertIn("31 October 2026", self.q("select body from documents where doc_id='letter_sm'")[0][0])

    def test_all_worry_evidence_resolves(self):
        v = View()
        for it in worry.items(v):
            for ref in it["evidence"]:
                v.describe(ref)  # raises KeyError if the citation is fabricated

    def test_no_future_leakage_in_any_answer(self):
        """Every citation shown under known_by=D1 must come from a source released by D1."""
        v = View(known_by=D1)
        for q in ["What should I worry about?", "How many open roles do we have?", "What is our ARR?",
                  "What is the attrition rate?", "What is going on with Siddharth?", "How much did the summit cost?"]:
            for ref, _ in ask(q, known_by=D1).cites:
                rel = self.db.execute("select released_on from sources where source_id=?", (v.ref_source(ref),)).fetchone()[0]
                self.assertLessEqual(rel, D1, (q, ref))
        b = worry.brief(known_by=D1, top=99)
        for it in b["top"]:
            for ref, _ in it["evidence"]:
                self.assertLessEqual(self.db.execute("select released_on from sources where source_id=?",
                                                     (v.ref_source(ref),)).fetchone()[0], D1)

    def test_nothing_known_before_release(self):
        b = worry.brief(known_by="2026-11-15")
        self.assertEqual(b["total_items"], 0)          # never padded
        self.assertEqual(ask("What should I worry about?", known_by="2026-11-15").status, "unknown")

    def test_individual_pay_never_emitted(self):
        out = View().describe("payroll:VX018:Feb-2026")
        for forbidden in ("110000", "1,10,000", "96800", "96,800", "gross"):
            self.assertNotIn(forbidden, out)
        full = worry.render(worry.brief(top=99))
        for amount in ("110000", "1,10,000", "400000", "4,00,000"):
            self.assertNotIn(amount, full)

    def test_brief_default_is_top_three_and_ordered(self):
        b = worry.brief(today="2026-11-17")
        self.assertEqual([i["id"] for i in b["top"]], ["atlas_ga", "eng_capacity", "runway_round"])
        self.assertEqual(b["age_days"], 17)
        scores = [i["score"] for i in b["top"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(i["evidence"] for i in b["top"]))


if __name__ == "__main__":
    unittest.main()
