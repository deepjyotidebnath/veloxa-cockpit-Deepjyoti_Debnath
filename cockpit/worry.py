"""'What should I worry about' ranking (CEO voice note T6a: open on the top three, no question).

Score = impact(1-5) x urgency(1-5) x confidence factor x share of evidence visible at this date.
Impact/urgency are OUR judgements (logged in DECISIONS.md D-06); confidence and the visible-evidence
share are mechanical. Every evidence ref is resolved against the database when the brief is built,
so an item can never cite a record that does not exist.
"""
import datetime as dt
from .view import View, EXPORT_DATE, inr

CONF = {"high": 1.0, "medium": 0.7, "low": 0.4}


def _aws_pct(v):
    r = v.db.execute("select amount_inr a from gl where vendor like 'Amazon%' order by effective_date").fetchall()
    return round((r[-1]["a"] / r[0]["a"] - 1) * 100) if len(r) > 1 else None


def _summit(v):
    return v.db.execute("select sum(amount_inr) s from gl where cost_centre='MKT-EVT'").fetchone()["s"]


def _pct_open(v):
    from . import eng
    j = eng.jira_open(v)
    if not j:
        return None
    pn = j["by_emp"]["VX007"]
    return j, pn


def items(v):
    """Each item: why/unknown may be callables of v so wording follows what has been released.
    `evidence` counts toward the evidence-share penalty; `evidence_later` is shown when released but never penalises
    (it did not exist at earlier dates, so its absence then is not a weakness of the earlier brief)."""
    aws = _aws_pct(v)
    jira = v.source_visible("SRC-JIRA")
    t6d = v.source_visible("SRC-T6d")
    out = [
        dict(id="atlas_ga",
             title=("Atlas (routing v3) GA slipped to 15 Dec in Jira; the engine is not 'feature-complete' as the board was told"
                    if jira else "Atlas (routing v3) GA slipped and no new date exists in any record"),
             impact=5, urgency=5, confidence="medium",
             why=("Jira moved GA from 15 Sep to 15 Dec on 2 Sep (by Vikram), while his call still says 'on track'. The Q3 board "
                  "update calls the engine feature-complete; Jira has the headline re-routing epic at 13 of 42 points. "
                  "No issue has been resolved since 17 Sep and 115 of 233 points are open."
                  if jira else
                  "GA was 15 Sep in the Q2 board update; the Q3 update says it was moved after a difficult August; "
                  "the CEO herself says customers were promised it for the festive season."),
             unknown=("Whether customers were told 15 Dec, and whether 15 Dec is achievable (arithmetic on recent pace says "
                      "it is doubtful, but Jira may lag)." if jira else
                      "The new GA date, and which customers were promised what. No source has either."),
             evidence=["documents:board_q2|on track for GA", "documents:board_q3|moved GA",
                       "transcripts:T1|festive season", "documents:letter_sm|launch timelines"],
             evidence_later=["versions:Atlas GA", "transcripts:T5|September-ish", "jira:ATLAS-29", "jira:ATLAS-27",
                             "documents:board_q3|feature-complete"]),
        dict(id="key_person",
             title=("Priya Nair, who holds most of Atlas, has resigned per the CEO (notice ~2 months, unconfirmed)"
                    if t6d else "Atlas rests on one engineer: Priya Nair holds 54% of open points and 70% of engine commits"),
             impact=5, urgency=4, confidence="medium",
             why=("The CEO's voice note says she resigned; no system record shows it yet. Her work: 62 of 115 open points, "
                  "all re-routing, 70% of atlas-engine commits. A 2-month notice from 19 Nov ends ~19 Jan, after the 15 Dec date."
                  if t6d else
                  "62 of 115 open Atlas points are hers, plus 70% of atlas-engine commits across two git identities, "
                  "with late-night commits (18%) that nobody else shows. The April plan had four owners; the tickets say one."),
             unknown=("Notice length, handover state, who takes re-routing. Nothing here says why, and I'm not guessing."
                      if t6d else "Whether anyone else could pick up re-routing; nothing records documentation or pairing."),
             evidence=["commits:VX007", "jira:ATLAS-19", "jira:ATLAS-29", "jira:ATLAS-70", "emails:04|Priya leads"],
             evidence_later=["transcripts:T6d|resigned", "emails:09|Atlas ownership"]),
        dict(id="eng_capacity", title="Engineering is stretched: pulse falling, two backend hires on hold, SRE on call every week",
             impact=4, urgency=4, confidence="medium",
             why="Engineering engagement fell 3.9 -> 3.1 in Jul-Sep (one of five did not respond); both backend reqs "
                 "were paused 12 Aug with 8 candidates in pipeline; an August reliability crunch needed paid on-call "
                 "cover and AWS spend rose; the Head of People is worried about one unnamed engineer."
                 + (" Three SEV1s hit routing-api in August; Sneha Kulkarni, the only SRE employee, is on the rota every "
                    "week of 17, and the contractor costs about Rs 1.4 L a month." if v.source_visible("SRC-PD") else ""),
             unknown="Who the engineer is (Deepa did not say; we do not guess), and the cause of the pulse drop. "
                     "Workload is the leading hypothesis, not a finding.",
             evidence=["pulse:Engineering:Jul-Sep 2026", "pulse:Engineering:Apr-Jun 2026", "reqs:REQ-014",
                       "reqs:REQ-015", "emails:06|until the round closes", "gl:JV-0902", "gl:JV-0921",
                       "transcripts:T3|one engineer", "transcripts:T1|holds the routing"],
             evidence_later=["incidents:INC-205", "emails:08|Third SEV1", "oncall:2026-08-17", "invoices:PIS-114",
                             "transcripts:T5|everyone's busy"]),
        dict(id="runway_round", title="Plans depend on a funding round that has not closed",
             impact=5, urgency=3, confidence="medium",
             why="Board update: runway 13 months and hiring paused 'while we close the round'. The CFO paused two reqs "
                 "to protect burn, and plans a wider freeze if the raise slips. The board wants 'the number by March'.",
             unknown="Cash balance, round status and what 'the number' is. Burn is defined inconsistently across "
                     "sources, so runway cannot be verified.",
             evidence=["documents:board_q3|Runway", "documents:board_q3|Hiring is paused",
                       "emails:06|Burn is the priority", "transcripts:T2|hiring freeze", "transcripts:T1|number by March"],
             evidence_later=["gl:JV-0688"]),
        dict(id="aws_cost", title="Cloud cost is climbing faster than revenue",
             impact=3, urgency=3, confidence="high",
             why=f"AWS postings rose {aws}% from April to September (largest single jump in the September posting, "
                 "i.e. August usage). ARR rose about 5% between the two board updates.",
             unknown="Whether the August spike was one-off (reliability work) or the new baseline.",
             evidence=["gl:JV-0421", "gl:JV-0821", "gl:JV-0921", "documents:board_q2|ARR", "documents:board_q3|ARR"]),
        dict(id="marketing_exit", title="Marketing: PMM gone, launch kit stranded, summit spend split across two vendor names",
             impact=3, urgency=3, confidence="medium",
             why=f"Siddharth Mehta's last day was 31 Oct; his letter cites unclear launch timelines. Backfill REQ-016 "
                 f"is open. Summit cost {inr(_summit(v))} across 'Sapphire Events Pvt Ltd' and 'Saphire Event Mgmt'; "
                 "the CFO says Nikhil's numbers never match hers."
                 + (" The launch kit has been ready since July and still shows a 22 Sep date." if v.source_visible("SRC-LAUNCH") else ""),
             unknown="Whether the two vendor names are one company, and what Marketing's own figures say.",
             evidence=["documents:letter_sm|last working day", "employees:VX013", "reqs:REQ-016",
                       "pulse:Marketing:Jul-Sep 2026", "gl:JV-0846", "gl:JV-0904", "transcripts:T2|never match"],
             evidence_later=["documents:launch_kit|planned 22 Sep", "emails:05|Launch kit is done"]),
        dict(id="payroll_control", title="A Feb joiner's first pay looks unprorated; query unanswered",
             impact=2, urgency=2, confidence="high",
             why="Feb payroll was run by a stand-in using the Jan sheet plus the new joiner; the joiner was paid for the "
                 "full 28 days though he joined on 3 Feb, and queried it on 6 Mar. Reply was 'will check'. "
                 "Overpayment is roughly 2/28 of one month's pay (amount withheld: salaries are restricted).",
             unknown="Whether it was ever corrected; no later record either way.",
             evidence=["emails:01|Used the Jan sheet", "emails:02|first payslip", "emails:03|check",
                       "payroll:VX018:Feb-2026", "employees:VX018"]),
    ]
    return out


def brief(known_by=None, as_of=None, top=3, today=None, db=None):
    v = View(known_by=known_by, as_of=as_of, db=db)
    ranked = []
    for it in items(v):
        shown, hidden = [], 0
        for ref in it["evidence"]:
            ok, text = v.cite(ref)  # raises KeyError on a bad ref
            if ok:
                shown.append((ref, text))
            else:
                hidden += 1
        later = [(r, tx) for r in it.get("evidence_later", []) for ok, tx in [v.cite(r)] if ok]
        if not shown:
            continue
        frac = len(shown) / len(it["evidence"])
        down = {"high": "medium", "medium": "low", "low": "low"}
        conf = it["confidence"] if frac == 1 else down[it["confidence"]]
        score = round(it["impact"] * it["urgency"] * CONF[conf] * frac, 1)
        ranked.append(dict(it, evidence=shown + later, confidence=conf, score=score,
                           partial=(f"{hidden} of {len(it['evidence'])} evidence records not yet released at this date"
                                    if hidden else None)))
    ranked.sort(key=lambda x: -x["score"])
    today_d = dt.date.fromisoformat(today) if today else dt.date.today()
    age = (today_d - dt.date.fromisoformat(as_of or EXPORT_DATE)).days
    return dict(data_as_of=as_of or EXPORT_DATE, age_days=age, known_by=known_by,
                top=ranked[:top], below_the_line=[(r["title"], r["score"]) for r in ranked[top:]],
                total_items=len(ranked))


def render(b):
    out = [f"WHAT TO WORRY ABOUT  (data as of {b['data_as_of']}"
           + (f", {b['age_days']} days old" if b["age_days"] > 0 else "")
           + (f"; knowledge as released by {b['known_by']}" if b["known_by"] else "") + ")", ""]
    for i, it in enumerate(b["top"], 1):
        out += [f"{i}. {it['title']}   [confidence: {it['confidence']}, score {it['score']}]",
                f"   Why: {it['why']}", f"   Don't know: {it['unknown']}"]
        if it["partial"]:
            out.append(f"   Note: {it['partial']}")
        out.append("   Evidence:")
        out += [f"     - {text}" for _, text in it["evidence"]]
        out.append("")
    n = len(b["below_the_line"])
    if n:
        out.append(f"{n} more item(s) ranked below the line (ask for the full list): "
                   + "; ".join(t for t, _ in b["below_the_line"]))
    out.append("Shows fewer than three if fewer than three items have evidence; never padded.")
    return "\n".join(out)
