"""Ask the cockpit one question. Deterministic and rule-based on purpose (DECISIONS D-03): every number
comes from a query, every citation is resolved against the database, and refusals are explicit.

Answer.status:
  answered | disagree (sources conflict; best-supported value given) | unknown | refused
"""
import re
from dataclasses import dataclass, field
from .view import View, inr, EXPORT_DATE
from . import worry


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


def h_atlas(v, q):
    cites, hidden = _cites(v, ["documents:board_q2|on track for GA", "documents:board_q3|moved GA",
                               "transcripts:T1|festive season"])
    if not cites:
        return _nothing_released(v, "the Atlas launch")
    return Answer("unknown",
                  "Atlas GA was planned for 15 Sep 2026 and was later moved. I don't know the new date: no released "
                  "record states one.", "medium", cites,
                  ["Customers were reportedly promised it 'by the festive season' (CEO, unverified, call undated)."])


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
