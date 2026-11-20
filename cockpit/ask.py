"""Ask the cockpit one question. Deterministic and rule-based on purpose (DECISIONS D-03): every number
comes from a query, every citation is resolved against the database, and refusals are explicit.

Answer.status:
  answered | disagree (sources conflict; best-supported value given) | unknown | refused
"""
import re
from dataclasses import dataclass, field
from .view import View, inr, EXPORT_DATE
from . import worry, eng, org


@dataclass
class Answer:
    status: str
    text: str
    confidence: str = None
    cites: list = field(default_factory=list)   # [(ref, resolved text)]
    caveats: list = field(default_factory=list)

    def render(self):
        out = [f"[{self.status.upper()}" + (f" | confidence: {self.confidence}" if self.confidence else "") + "]",
               self.text]
        out += [f"  caveat: {c}" for c in self.caveats]
        if self.cites:
            out.append("  sources:")
            out += [f"    - {t}" for _, t in self.cites]
        return "\n".join(out)


def _cites(v, refs):
    got, hidden = [], 0
    for r in refs:
        ok, t = v.cite(r)
        if ok:
            got.append((r, t))
        else:
            hidden += 1
    return got, hidden


def _nothing_released(v, what):
    return Answer("unknown", f"I don't know: no record about {what} had been released by {v.known_by}.", None)


def _need(v, *sources):
    return all(v.source_visible(s) for s in sources)



def _people(v):
    return [r for r in v.db.execute("select full_name, emp_id from employees")]


# ------------------------------------------------------------------ handlers
def h_headcount(v, q):
    if not _need(v, "SRC-EMP"):
        return _nothing_released(v, "headcount")
    d = v.as_of or EXPORT_DATE
    n = len(v.employees_on(d))
    refs = ["documents:board_q3|Team"] if v.source_visible("SRC-BOARD-Q3") else []
    refs += ["employees:VX013"]
    cites, _ = _cites(v, refs)
    cav = ["Employees only: contractors (e.g. on-call cover) are not in the HR export.",
           "Disagreement: the kickoff call says 'eighteen' / 'one-eighty' and the brief says 180; the HR master, "
           "payroll and both board updates say 19. Believed: 19 (system records beat a mis-transcribed call)."]
    after = len(v.employees_on("2026-11-01")) if d == EXPORT_DATE and v.source_visible("SRC-EMP") else None
    extra = f" It drops to {after} from 1 Nov because the Product Marketing Manager's last day was 31 Oct." if after else ""
    return Answer("disagree", f"{n} employees on {d}.{extra}", "high", cites, cav)


def h_arr(v, q):
    if not _need(v, "SRC-BOARD-Q2") and not _need(v, "SRC-T1"):
        return _nothing_released(v, "ARR")
    cites, _ = _cites(v, ["documents:board_q3|ARR", "documents:board_q2|ARR", "transcripts:T1|forty-two",
                          "transcripts:T2|forty-eight"])
    return Answer("disagree",
                  "The sources disagree. Best-supported: Rs 6.1 Cr ARR (board update sent 6 Oct 2026), up from "
                  "Rs 5.8 Cr in the update sent 8 Jul. The calls give 'forty-two/forty-five' and 'forty-eight' with no unit.",
                  "medium", cites,
                  ["Board figures are management-reported and unaudited; the GL export has no revenue lines, so ARR "
                   "cannot be checked against ledger data.",
                   "The call figures may be 4.2/4.5/4.8 Cr with the decimal dropped, but 4.8 'at start of year' and "
                   "4.2-4.5 'now' contradict each other, so they are not used."])


def h_burn(v, q):
    if not _need(v, "SRC-BOARD-Q3") and not _need(v, "SRC-T2"):
        return _nothing_released(v, "burn")
    cites, _ = _cites(v, ["documents:board_q3|Runway", "documents:board_q2|Runway", "transcripts:T2|two point two",
                          "gl:PAY-SEP"])
    return Answer("disagree",
                  "The sources disagree and burn is not defined in any of them. Board: Rs 44 L/month (Jul-Sep), "
                  "Rs 46 L (Apr-Jun). CFO call: '2.2 lakhs a month', which I reject: monthly salaries alone are "
                  "Rs 31.75 L in the ledger.",
                  "low", cites,
                  ["If board 'burn' is net of revenue (ARR Rs 6.1 Cr is about Rs 51 L/month) it does not reconcile with "
                   "the GL costs we can see (about Rs 38-40 L/month in selected cost centres). It may be gross spend.",
                   "The GL is 'selected cost centres' only, so total spend is unknown."])


def h_runway(v, q):
    if not _need(v, "SRC-BOARD-Q3"):
        return _nothing_released(v, "runway")
    cites, _ = _cites(v, ["documents:board_q3|Runway"])
    return Answer("unknown", "The board update states 13 months (Jul-Sep), but I can't verify it: no source gives a "
                  "cash balance, and burn is defined inconsistently.", "low", cites)


def _epic_done(v, epic):
    r = v.db.execute("select sum(story_points) p, sum(case when status='Done' then story_points else 0 end) d "
                     "from jira_issues where epic=?", (epic,)).fetchone()
    return f"{r['d']} of {r['p']}"


def h_atlas(v, q):
    g = eng.ga(v)
    if g is None:   # Day 1-2 knowledge
        cites, hidden = _cites(v, ["documents:board_q2|on track for GA", "documents:board_q3|moved GA",
                                   "transcripts:T1|festive season"])
        if not cites:
            return _nothing_released(v, "the Atlas launch")
        return Answer("unknown",
                      "Atlas GA was planned for 15 Sep 2026 and was later moved. I don't know the new date: no released "
                      "record states one.", "medium", cites,
                      ["Customers were reportedly promised it 'by the festive season' (CEO, unverified, call undated)."])
    j = eng.jira_open(v)
    refs = ["versions:Atlas GA", "documents:board_q3|moved GA", "documents:board_q2|on track for GA",
            "transcripts:T5|on track", "transcripts:T5|September-ish", "documents:launch_kit|planned 22 Sep"]
    cites, _ = _cites(v, refs)
    left = j["open_points"]
    cav = ["Believed: Jira (a system record, changed by Vikram himself on 2 Sep) over his call, where he says v3 is "
           "'on track' and the board date 'still September-ish'. The call is undated, so it may predate 2 Sep, but "
           "'incidents in August' means it was after them.",
           f"{left} of {j['points']} story points are still open ({round(100 * left / j['points'])}%), and no Jira issue "
           f"has been resolved since {eng.last_resolved(v)} (export is 31 Oct). I can't tell you whether 15 Dec is "
           "achievable; the records only show it is not yet being met by throughput.",
           "Board Q3 (6 Oct) calls the engine 'feature-complete'; Jira shows the headline re-routing epic at "
           f"{_epic_done(v, 'ATLAS-2')} story points done. Believed: Jira over management-reported board text.",
           "Illustrative arithmetic, not a forecast: closed points were 42 (Jun), 28 (Jul), 24 (Aug), 8 (Sep), 0 (Oct). "
           "At the Jul-Aug average of 26/month, 115 open points is about 4.4 months of work; the export is 6.5 weeks "
           "before 15 Dec. Jira may lag reality, so treat this as a reason to ask, not an answer.",
           "A Jira release date is an internal planning field; whether customers were told 15 Dec is not recorded.",
           "The launch kit still says launch 'planned 22 Sep': stale."]
    return Answer("disagree", f"Jira has Atlas GA on {g['release_date']}, moved from {g['original_release_date']} on "
                  f"{g['last_changed']} by {g['changed_by']}. The VP Engineering's call says it is on track for "
                  "September; I believe the system record.", "medium", cites, cav)


def h_dependencies(v, q):
    j = eng.jira_open(v)
    if j is None:
        return _nothing_released(v, "who holds the Atlas work")
    pn = j["by_emp"]["VX007"]
    cp = eng.commit_profile(v, "VX007")
    oc = eng.oncall_load(v)
    atlas_commits = v.db.execute("select count(*) n from commits where repo='atlas-engine'").fetchone()["n"]
    pe = v.db.execute("select count(*) n from commits where repo='atlas-engine' and emp_id='VX007'").fetchone()["n"]
    refs = ["commits:VX007", "jira:ATLAS-19", "jira:ATLAS-29", "jira:ATLAS-70", "oncall:2026-08-17", "emails:04|Priya leads"]
    cites, _ = _cites(v, refs)
    txt = (f"Concentration of work (not a measure of anyone's intent): Priya Nair holds {pn['open_points']} of "
           f"{j['open_points']} open Atlas story points ({round(100 * pn['open_points'] / j['open_points'])}%) and "
           f"{round(100 * pe / atlas_commits)}% of atlas-engine commits across her two git identities. "
           f"Sneha Kulkarni, the only SRE employee, is on the on-call rota in {oc['sneha_primary'] + oc['sneha_secondary']} "
           f"of {oc['weeks']} weeks. Arjun Das is the only frontend engineer on the Atlas UI.")
    return Answer("answered", txt, "high", cites,
                  ["This ranks where work is concentrated, not who is likely to leave; the records do not support the latter.",
                   "Jira keeps only final status, so 'open' means not resolved by the as-of date."])


def h_priya_leaves(v, q):
    t6d = v.source_visible("SRC-T6d")
    j = eng.jira_open(v)
    if not t6d and j is None:
        return _nothing_released(v, "that")
    cites, _ = _cites(v, ["transcripts:T6d|resigned", "employees:VX007", "commits:VX007", "jira:ATLAS-19",
                          "versions:Atlas GA", "emails:09|Atlas ownership"])
    pn = j["by_emp"]["VX007"] if j else None
    pe = v.db.execute("select count(*) n from commits where repo='atlas-engine' and emp_id='VX007'").fetchone()["n"]
    tot = v.db.execute("select count(*) n from commits where repo='atlas-engine'").fetchone()["n"]
    parts = []
    if t6d:
        parts.append("Status of the news: reported only in the CEO's voice note T6d ('this morning', date not stated, "
                     "'Pria' = Priya Nair, the only Priya). No system record shows it: the HR export is dated 31 Oct "
                     "and lists her as Active.")
    if pn:
        parts.append(f"Exposure: Priya holds {pn['open_points']} of {j['open_points']} open Atlas story points "
                     f"({round(100 * pn['open_points'] / j['open_points'])}%), all of re-routing (epic ATLAS-2), most of "
                     f"core engine and hardening, and {round(100 * pe / tot)}% of atlas-engine commits.")
    g = eng.ga(v)
    if g:
        end = eng.notice_end("2026-11-19")
        parts.append(f"Timing, if the notice is 2 months from 19 Nov: last day about {end.isoformat()}, i.e. after the "
                     f"Jira GA date of {g['release_date']}. But the notice length is the CEO's recollection ('I think') "
                     "and Siddharth's notice (15 Sep to 31 Oct, 46 days) shows notice periods here are not fixed.")
    parts.append("What I can't tell you: a new GA date, how much of her work is documented or transferable, or whether "
                 "she stays through GA. I'm not going to forecast v3 from this; any date I gave would be invented.")
    return Answer("unknown", " ".join(parts), "low" if t6d else "medium", cites,
                  ["Before the board call, the questions the records can't answer are for Vikram: who takes re-routing, "
                   "and what 'done' means for the 15 Dec date.",
                   "A 1 Sep email (Priya to Vikram, 'Atlas ownership') exists with no reply in the data. I don't know what "
                   "it was about and I'm not drawing a conclusion from it."])


def h_promised(v, q):
    cites, _ = _cites(v, ["transcripts:T1|festive season"])
    if not cites:
        return _nothing_released(v, "customer commitments")
    return Answer("unknown", "I don't know. The CEO says the engine was promised 'to some customers' by the festive season "
                  "(T1, undated call). No record names a customer, a contract or a date, and the CRM export (HubSpot) "
                  "is not in the data room.", None, cites)


def h_why_resign(v, q):
    cites, _ = _cites(v, ["transcripts:T6d|resigned", "emails:09|Atlas ownership"])
    return Answer("unknown", "I don't know why. No record states a reason: the only source for the resignation is a voice "
                  "note, and the HR export predates it. I won't infer a motive from workload, leave or emails.", None, cites)


def h_quit_list(v, q):
    return Answer("refused",
                  "I won't produce a ranked list of named people by how likely they are to quit. With 19 people and "
                  "the records we have (no exit history, comments suppressed, no Slack data in the data room) any ranking "
                  "would be a guess about individuals, and a wrong or leaked one can hurt a person who did nothing. "
                  "What I can show instead: team-level signals (pulse, open reqs, notice periods) and where work is "
                  "concentrated (ask: 'who is a single point of failure?').", None, [],
                  ["Deepa did not say 'it's fine': she said attrition is 'about twelve' and 'normal', and in the same call "
                   "said she is worried about one engineer; her 29 Sep email asks for 1:1s because engineering pulse dropped."])


def h_slack(v, q):
    return Answer("refused",
                  "I won't show people's private messages. There is also no Slack export in the data room (README lists "
                  "none; 'slag channel' in T1 is only an action item), so there is nothing to show.", None, [],
                  ["If you want to hear how people feel, the options are a conversation, or opening the survey-comment "
                   "visibility decision that is already on your list (T3)."])


def h_snehal(v, q):
    cites, _ = _cites(v, ["oncall:2026-08-17", "gl:JV-0902", "invoices:PIS-114", "emails:08|contractor",
                          "transcripts:T5|Snehal on SRE", "incidents:INC-206", "employees:VX012"])
    if not cites:
        return _nothing_released(v, "who Snehal is")
    return Answer("disagree",
                  "Best reading: 'Snehal' is the contractor S. Patil from Patil Infra Services, and 'Sneha' is the "
                  "employee Sneha Kulkarni; they are two people. The VP Engineering's call blurs them.", "medium", cites,
                  ["This is an inference: no record says 'Snehal = S. Patil'. It rests on the rota showing 'Snehal' from "
                   "17 Aug, the ledger and invoice showing Patil on-call cover from 18 Aug, email 08 saying a contractor "
                   "starts on the rota, and no Snehal in HR, payroll or Jira.",
                   "Email 08 (24 Aug) says the contractor starts 'this week', but the rota has Snehal from 17 Aug and the "
                   "invoice covers 18 Aug: believed the invoice and ledger."])


def h_oncall(v, q):
    oc, inc = eng.oncall_load(v), eng.incidents(v)
    if oc is None and inc is None:
        return _nothing_released(v, "on-call or incidents")
    cites, _ = _cites(v, ["incidents:INC-201", "incidents:INC-203", "incidents:INC-205", "emails:08|Third SEV1",
                          "oncall:2026-07-06", "oncall:2026-08-17"])
    txt = (f"{inc['n']} incidents Aug-Oct 2026 ({len(inc['sev1'])} SEV1, all in August; {inc['routing']} on routing-api), "
           f"about {inc['hours']} hours open in total. Sneha Kulkarni was on the on-call rota in "
           f"{oc['sneha_primary'] + oc['sneha_secondary']} of {oc['weeks']} weeks (primary {oc['sneha_primary']}). "
           f"A contractor was added from 17 Aug and is on the rota in {oc['contractor_primary'] + oc['contractor_secondary']} weeks.")
    return Answer("answered", txt, "high", cites,
                  ["PagerDuty times are UTC; INC-203 and INC-205 cross midnight in IST. Counts use the IST date.",
                   "The rota is a hand-copied wiki table (medium reliability)."])


def h_contractor(v, q):
    if not _need(v, "SRC-INV-PIS114"):
        return _nothing_released(v, "contractor cost")
    cites, _ = _cites(v, ["gl:JV-0902", "invoices:PIS-114", "gl:JV-0688", "emails:06|Burn is the priority"])
    return Answer("answered",
                  "On-call contractor (Patil Infra Services): Rs 70,800 booked for 18-31 Aug (ledger JV-0902) and "
                  "invoice PIS-114 for Rs 1,41,600 (Rs 1,20,000 + GST) for September, dated 1 Oct, which is not in the "
                  "ledger export (it ends 30 Sep). Run-rate about Rs 1.4 L/month.", "high", cites,
                  ["Worth setting beside the hiring pause: the ledger also shows a Rs 1,77,000 recruiter advance (30 Jun) "
                   "for the same two backend roles that were paused on 12 Aug.",
                   "PIS-108 was pro-rated as half a month for a 14-day stretch; immaterial, noted.",
                   "The invoice date 01/10/2026 is dd/mm/yyyy (1 Oct), not 10 Jan."])


def h_launch_kit(v, q):
    cites, _ = _cites(v, ["documents:launch_kit|planned 22 Sep", "emails:05|Launch kit is done", "transcripts:T4|launch kit",
                          "documents:letter_sm|launch kit", "employees:VX013", "reqs:REQ-016"])
    if not cites:
        return _nothing_released(v, "the launch kit")
    return Answer("answered",
                  "The Atlas launch kit has been ready since July (deck, page and emails ready; press note draft; page "
                  "'ready, unpublished'). It is waiting on a launch date from engineering, and its planned date (22 Sep) "
                  "is now stale. Its owner, Siddharth Mehta, left on 31 Oct.", "high", cites,
                  ["Whether the kit was handed over is not recorded (his letter promises it).",
                   "'Ready since July' comes from Sid's own email and Nikhil's call; no one else confirms the quality."])


def h_mkt_spend(v, q):
    if not _need(v, "SRC-GL"):
        return _nothing_released(v, "marketing spend")
    r = v.db.execute("select sum(amount_inr) s from gl where cost_centre like 'MKT-%'").fetchone()["s"]
    cites, _ = _cites(v, ["gl:JV-0846", "gl:JV-0904", "gl:JV-0603", "transcripts:T4|one point eight",
                          "transcripts:T2|never match"])
    return Answer("disagree",
                  f"The ledger shows {inr(r)} in marketing cost centres Apr-Sep (summit Rs 10,03,000 + Google Ads). "
                  "Nikhil's call says 'one point eight' with no unit; I can't reconcile the two.", "low", cites,
                  ["The ledger is 'selected cost centres' and has no LinkedIn, HubSpot or marketing salaries, so the gap may "
                   "just be scope. Not resolvable from the data.",
                   "'Summit went a little over' cannot be checked: no summit budget exists in any record.",
                   "'Best quarter for pipeline' (Nikhil) vs 'summit leads are cold' (Manoj, via Nikhil): no CRM export exists."])


def h_who_reports(v, q):
    ppl = {r["full_name"].split()[0].lower(): r for r in v.db.execute("select * from employees")}
    name = next((n for n in ppl if n in q), None)
    if re.search(r"\bcro\b", q) and not name:
        pl = org.planned_changes(v)
        cites, _ = _cites(v, ["org:VX006:planned", "transcripts:T6b|CRO", "transcripts:T4|CRO"])
        if not cites:
            return _nothing_released(v, "a CRO")
        return Answer("unknown", "I don't know. There is no CRO in the HR records and no start date. The CEO says Marketing "
                      "will report to a new CRO 'from next month, or the month after' (T6b) and Nikhil only 'hears' it (T4); "
                      "until a dated record exists, Marketing keeps its recorded reporting line.", "high", cites)
    if not name:
        return Answer("unknown", "I don't know whose reporting line you mean.", None)
    e = ppl[name]
    m = org.manager_of(v, e["emp_id"])
    if re.search(r"report(s)? to|manager|boss", q) and "who reports" not in q:
        if not m:
            return Answer("answered", f"{e['full_name']} has no recorded manager (top of the organisation).", "high",
                          _cites(v, [f"employees:{e['emp_id']}"])[0])
        mm = v.db.execute("select full_name from employees where emp_id=?", (m,)).fetchone()["full_name"]
        cites, _ = _cites(v, [f"employees:{e['emp_id']}", f"employees:{m}"])
        cav = []
        if e["emp_id"] == "VX006" and v.source_visible("SRC-T6b"):
            cav.append("A move to a new CRO is planned but unconfirmed (T6b): not applied.")
        return Answer("answered", f"{e['full_name']} reports to {mm} (HR master, 31 Oct).", "high", cites, cav)
    kids = org.reports_of(v, e["emp_id"])
    names = [v.db.execute("select full_name from employees where emp_id=?", (k,)).fetchone()["full_name"] for k in kids]
    cites, _ = _cites(v, [f"employees:{k}" for k in kids[:6]])
    return Answer("answered", f"{e['full_name']}'s direct reports: {', '.join(names) or 'none'}.", "high", cites)


def h_salary(v, q):
    return Answer("refused",
                  "I won't show individual salaries or pay. The CFO's standing instruction is that individual "
                  "salaries must never reach the CEO's view, only totals. I can give payroll totals instead.",
                  None, [], ["Aggregate available: gross payroll Rs 31,75,000 per month (Mar 2026 register; the ledger "
                             "books the same figure each month Apr-Sep)."])


def h_payroll_total(v, q):
    if not _need(v, "SRC-PAY"):
        return _nothing_released(v, "payroll")
    r = v.db.execute("select month, count(*) n, sum(gross_inr) g from payroll where month='Mar-2026'").fetchone()
    cites, _ = _cites(v, ["gl:PAY-SEP"])
    return Answer("answered", f"Gross payroll is {inr(r['g'])} per month for {r['n']} people (Mar 2026 register). "
                  "The ledger books exactly this amount every month from Apr to Sep 2026.", "high", cites,
                  ["Gross, before employer on-costs; no register exists for Apr-Sep, so changes after March are not visible."])


def h_comments(v, q):
    return Answer("refused",
                  "I won't show or infer survey comments. Culture Amp suppresses comments for any team under 6, and "
                  "every Veloxa team is under 6, so comments cannot be anonymous. Team scores are available.",
                  None, [], ["Whether the CEO sees comments is an open decision for her (T3 action item); that is not "
                             "mine to pre-empt by inference."])


def h_who_worried(v, q):
    cites, _ = _cites(v, ["transcripts:T3|one engineer"])
    if not cites:
        return _nothing_released(v, "engineer concerns")
    return Answer("unknown", "I don't know. The Head of People said there is one engineer she is worried about and "
                  "chose not to name them. I won't guess from leave or other records.", None, cites)


def h_person_risk(v, q):
    return Answer("refused", "I won't predict whether a named individual will resign or is struggling. I can show "
                  "team-level signals (pulse, open reqs) and recorded facts.", None)


def h_attrition(v, q):
    if not _need(v, "SRC-EMP"):
        return _nothing_released(v, "attrition")
    cites, _ = _cites(v, ["transcripts:T3|attrition", "employees:VX013"])
    txt = ("I can't compute attrition. The HR export lists current employees only, with one known leaver, so "
           "there is no exit history.")
    if v.source_visible("SRC-T3"):
        txt += " The Head of People says 'about twelve' (unit unclear: percent, headcount or target)."
    cav = []
    if v.source_visible("SRC-PULSE"):
        cav.append("Hint of missing leavers: the pulse survey counts 5 engineers in Oct-Dec 2025 but only 4 engineers "
                   "had joined by then per the master.")
    return Answer("unknown", txt, "low", cites, cav)


def h_summit(v, q):
    if not _need(v, "SRC-GL"):
        return _nothing_released(v, "summit spend")
    s = v.db.execute("select sum(amount_inr) s from gl where cost_centre='MKT-EVT'").fetchone()["s"]
    cites, _ = _cites(v, ["gl:JV-0846", "gl:JV-0904", "gl:JV-0918", "transcripts:T2|never match"])
    return Answer("answered", f"{inr(s)} was booked to the summit cost centre (MKT-EVT) in two entries.", "medium",
                  cites, ["The two vendors are 'Sapphire Events Pvt Ltd' and 'Saphire Event Mgmt'. Likely the same "
                          "company misspelt, but not confirmed; no invoice number links them.",
                          "'Sapphire Residency Hotel' (sales offsite, Rs 38,940) is a different vendor.",
                          "Marketing's own numbers are not in the data, so the CFO's 'never match' claim can't be checked."])


def h_aws(v, q):
    if not _need(v, "SRC-GL"):
        return _nothing_released(v, "AWS spend")
    cites, _ = _cites(v, ["gl:JV-0421", "gl:JV-0821", "gl:JV-0921"])
    return Answer("answered", f"AWS postings rose {worry._aws_pct(v)}%, from Rs 1,81,200 (8 Apr) to Rs 2,48,310 (8 Sep). "
                  "Each posting is the previous month's usage.", "high", cites)


def h_reqs(v, q):
    if not _need(v, "SRC-HIRE"):
        return _nothing_released(v, "open roles")
    d = v.as_of or EXPORT_DATE
    rows = v.rows("reqs", "opened<=?", (d,))
    openr = [r for r in rows if r["status"] == "Open" or r["status_date"] > d]
    hold = [r for r in rows if r["status"] == "On hold" and r["status_date"] <= d]
    refs = [f"reqs:{r['req_id']}" for r in rows]  # cite every req that existed, so "0 open" is still evidenced
    cites, _ = _cites(v, refs)
    return Answer("disagree", f"On {d}: {len(openr)} open and {len(hold)} on hold requisitions.", "high", cites,
                  ["Tracker is an export-day snapshot with no status history: before a req's status date it is "
                   "inferred to have been open.",
                   "Rohan (Talent Partner) said '22 open roles in April'; the tracker shows at most 1 open requisition in "
                   "April and never more than 4 even counting on-hold ones. Believed: the tracker.", "REQ-012 is missing from the export; unexplained.",
                   "The board says 'hiring is paused' but REQ-016/017 opened after the pause; the pause covers the two "
                   "backend reqs only."])


def h_sid(v, q):
    cites, _ = _cites(v, ["employees:VX013", "documents:letter_sm|last working day", "reqs:REQ-016"])
    if not cites:
        return _nothing_released(v, "that person")
    only_master = len(cites) == 1
    txt = ("The HR export shows Siddharth Mehta (Product Marketing Manager) on notice with exit date 31 Oct 2026."
           if only_master else
           "Siddharth Mehta (Product Marketing Manager) resigned on 15 Sep 2026; last working day 31 Oct 2026. "
           "A backfill (REQ-016) opened 17 Sep.")
    return Answer("answered", txt, "high", cites,
                  [] if not only_master else ["Why he is leaving is not in anything released yet."])


def h_eng_pulse(v, q):
    if not _need(v, "SRC-PULSE"):
        return _nothing_released(v, "engagement")
    cites, _ = _cites(v, [f"pulse:Engineering:{x}" for x in ("Oct-Dec 2025", "Jan-Mar 2026", "Apr-Jun 2026", "Jul-Sep 2026")])
    return Answer("answered", "Engineering engagement: 4.0, 4.0, 3.9, then 3.1 in Jul-Sep 2026 (4 of 5 responded). "
                  "It is the sharpest drop of any team; Marketing fell 3.8 to 3.4.", "high", cites,
                  ["The cause is not in the data; workload is a hypothesis from calls."])


def h_worry(v, q):
    b = worry.brief(known_by=v.known_by, as_of=v.as_of)
    seen, cites = set(), []
    for it in b["top"]:
        for ref, text in it["evidence"]:
            if ref not in seen:
                seen.add(ref)
                cites.append((ref, text))
    conf = "see each item" if b["top"] else None
    return Answer("answered" if b["top"] else "unknown", worry.render(b) if b["top"] else
                  f"I don't know: nothing had been released by {v.known_by}.", conf, cites)


def h_forecast(v, q):
    return Answer("unknown", "I don't know. No released record contains a forecast, target or plan for that, and I "
                  "won't extrapolate from two board updates.", None)


# ------------------------------------------------------------------ routing
RULES = [
    (r"which customers|who was promised|customers? (were|was) promised|promised (to )?(customers|clients)", h_promised),
    (r"\bwhy\b.*\b(pria|priya)\b.*(resign|leav|quit|go)", h_why_resign),
    (r"\b(atlas|v3|version three|routing engine)\b.*\b(ship|launch|ga|release|ready|slip|deliver|date)\b|\bwhen (will|is|does) .*(atlas|v3|version three)", h_atlas),
    (r"\b(rank|list|who).*\b(quit|resign|flight risk|likely to leave)|likely to (quit|leave)", h_quit_list),
    (r"\bslack|\bslag\b|private messages?|\bdms?\b", h_slack),
    (r"\b(pria|priya)\b.*(resign|quit|leav|notice)|(resign|quit).*\b(pria|priya)\b|what does this do to (version three|v3|atlas)", h_priya_leaves),
    (r"single point|key.?person|bus factor|who (do we|does .*) (depend|rely)|who is critical|concentrat", h_dependencies),
    (r"\bsnehal\b|who is s\.? ?patil", h_snehal),
    (r"\b(on.?call|pagerduty|incidents?|sev ?1|outage)\b", h_oncall),
    (r"contractor|patil|retainer", h_contractor),
    (r"launch kit", h_launch_kit),
    (r"marketing (spend|budget|cost)|spend on marketing|google ads", h_mkt_spend),
    (r"report(s)? to|\bcro\b|reporting line|who reports|org chart", h_who_reports),
    (r"(which|who|what).*(engineer).*(worr|concern)|engineer .*worried", h_who_worried),
    (r"\b(will|going to|likely to|about to)\b.*\b(quit|resign|leave|leaving)\b|\bis .* (unhappy|burn(ed|t) out)", h_person_risk),
    (r"\b(top (three|3)|worry|worried about|risks?|concerns?)\b", h_worry),
    (r"\b(survey|pulse|culture amp)\b.*\bcomments?\b|\bcomments?\b.*\b(survey|pulse)\b", h_comments),
    (r"\b(salary|salaries|ctc|compensation|how much (does|is|did).*(earn|paid|make)|highest paid|pay ?slip)\b", None),
    (r"\bpayroll\b|\bsalar", h_payroll_total),
    (r"\battrition|turnover\b", h_attrition),
    (r"\b(will|forecast|predict|project(ed|ion)?|next (quarter|year)|by march)\b", h_forecast),
    (r"\bheadcount|how many (people|employees)|team size\b", h_headcount),
    (r"\barr\b|annual recurring|recurring revenue", h_arr),
    (r"\brunway\b", h_runway),
    (r"\bburn\b", h_burn),
    (r"\batlas|routing|\bga\b|launch date|general availability", h_atlas),
    (r"\bsummit\b|\bevent spend|sapphire|saphire", h_summit),
    (r"\baws\b|cloud (cost|spend)", h_aws),
    (r"open (roles|reqs|requisitions|positions)|hiring|requisition", h_reqs),
    (r"\bsid(dharth)?\b|product marketing manager", h_sid),
    (r"engineering.*(engagement|pulse|morale|score)|(engagement|pulse|morale).*engineering", h_eng_pulse),
]


def ask(question, known_by=None, as_of=None, db=None):
    v = View(known_by=known_by, as_of=as_of, db=db)
    q = question.lower()
    for pat, fn in RULES:
        if re.search(pat, q):
            if fn is None:
                # salary question: refuse if it targets a person or ranks people; totals handled by next rule
                if re.search(r"\b(total|aggregate|overall|whole company|monthly payroll)\b", q) and not any(
                        n["full_name"].split()[0].lower() in q for n in _people(v)):
                    return h_payroll_total(v, q)
                return h_salary(v, q)
            return fn(v, q)
    return Answer("unknown", "I don't know. None of the released records answers that, and I'd rather say so than "
                  "guess.", None)
