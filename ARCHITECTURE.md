# Architecture

*Status: written on 17 Nov, after the Day 1 deadline (Mon 16 Nov, 11:59 PM IST). The commit history shows the true
date. Revised as the design changes; see the changelog at the bottom.*

## Shape

```
data/dayN/*  --(cockpit/db.py)-->  build/veloxa.db  --(View: known_by, as_of)-->  ask.py / worry.py  --> CLI
 raw, as released                  one SQLite file     point-in-time filter        answers + citations
```

Everything is standard-library Python + SQLite. The database is rebuilt from `data/` on every run, so it is never
a source of truth. The CSV/markdown in `data/` is.

## The one idea that matters: two clocks

Every record carries two dates:

- `released_on`: the day the hackathon pack handed it to us (16 Nov for Day 1, 17 Nov for Day 2, ...).
- `effective_date`: when it happened inside Veloxa (NULL when unknown, e.g. undated call transcripts).

`View(known_by, as_of)` filters on each independently. **"What did we know on date X?"** is `known_by`; **"what was
true in the company on date X?"** is `as_of`. They differ materially: the data room is an export from 31 Oct that we
only learned about on 16 Nov, and the resignation letter is dated 15 Sep but was unknown to us until 17 Nov.
A test (`test_no_future_leakage_in_any_answer`) checks that every citation shown under `known_by=D` comes from a source
released on or before D.

## Data model

`sources` (id, kind, release date, effective date, reliability, notes) is the spine; every other row points at one.
Tables: `employees`, `gl`, `payroll`, `reqs`, `pulse`, `leave`, `emails`, `documents`, `transcripts`.
Entity resolution (names written differently across files) is explicit: leave-register abbreviations are mapped to
`emp_id` in the CSV, and ambiguous vendor names are **not** merged (DECISIONS D-09).

## Source trust (DECISIONS D-04)

System exports > dated documents/emails > management-reported figures (board) > machine transcripts.
A transcript number is only used when something else corroborates it. Every conflict gets an entry in
`TRANSCRIPT_NOTES.md` stating which side was believed and why.

## Answer layer

`ask.py` is deliberately **rule-based, not an LLM** (D-03). Each handler runs queries, builds the sentence from the
results, resolves every citation against a real row, and returns an `Answer` with a status
(`answered | disagree | unknown | refused`), a confidence, citations and caveats. Unrouted questions return "I don't
know". Refusals: individual pay, survey comments, predictions about named people, forecasts (D-05).

`worry.py` ranks evidence-backed items by impact x urgency x confidence x visible-evidence share. Evidence not yet
released is dropped and lowers confidence rather than leaking.

## Day 3/4 additions

- **Engineering tables** (`jira_issues`, `jira_versions`, `incidents`, `oncall`, `commits`, `invoices`) with explicit entity
  resolution at load time: Jira initials, Priya's two git identities, Sneha (employee) vs Snehal (contractor).
- **`eng.py`** derives work-concentration facts (share of open points and commits, on-call weeks, incident counts). It measures
  work; it predicts nothing about anyone.
- **`org.py` + `org_history`** make reporting lines effective-dated; 'planned' rows (T6b) exist but are inert until a dated record appears.
- **Agents (`agents.py`)**: memory = dated records read through `View`, so release dates bind them too; personality is
  invented, labelled in every reply and logged (A-16..A-29). Pay, survey comments and speculation about colleagues are refused.
- **Simulation (`sim.py`)** writes to `build/sim.db`, a separate file; the evidence database cannot contain synthetic rows.
- **Worry list**: `evidence_later` lets new evidence strengthen an item without retroactively weakening earlier briefs.

## Source trust, with worked examples (D-04, D-18)
Exports > dated documents/emails > board prose > machine transcripts. Jira beat Vikram's call on the GA date (N-28) and the board's
"feature-complete" (N-29); the ledger and invoice beat an email's "starts this week" (N-30).

## Not built
- No LLM in the loop (D-03): fluent paraphrase of questions and richer agent dialogue would need one, constrained to retrieve and phrase, never to supply facts.
- No Slack/CRM data exist, so nothing is built on them.

## Changelog
- 17 Nov: first version. Day 1 + Day 2 loaded; cockpit, worry view, 30 QA cases + 11 integrity tests.
- 20 Nov: Day 3/4 loaded; engineering tables, org history, agents, simulation; 49 QA cases; point-in-time brief reproducible per date.
