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

## Not built yet

- 14 agent colleagues (roster is fixed by the data: 5 Engineering, 3 Finance, 3 People & Ops, 3 Marketing). Plan:
  each agent's memory is an append-only list of dated records filtered through the same `View`, so an agent cannot
  "remember" something its source had not released.
- Day 3/4 data; stretch simulation after 31 Oct.

## Changelog
- 17 Nov: first version. Day 1 + Day 2 loaded; cockpit, worry view, 30 QA cases + 11 integrity tests.
