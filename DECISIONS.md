# Decisions (choices that could be defended either way)

**D-01 SQLite built from files committed in `data/`.** Alternatives: Postgres (more setup, nothing gained at 20 sources),
vector store (answers must be exact numbers with citations, not "similar passages"). Cost: no full-text search yet.

**D-02 Two clocks per record (`released_on`, `effective_date`).** Alternative: one date. A single date can't tell
"true on 30 Sep" from "known on 16 Nov", and the task asks for both readings. Cost: every loader must set both.

**D-03 Rule-based answer engine, not an LLM.** Deterministic, every sentence traceable to a query, easy to test
against expected answers. Cost: brittle to phrasing (a new phrasing falls through to "I don't know", which is the safe
failure). An LLM may later help *parse the question*, never supply a fact.

**D-04 Source trust order:** exports > dated documents/emails > board (management-reported) > transcripts. Exceptions
are explicit and logged. Rationale: the brief says exports are more reliable; transcripts are machine-generated and
speakers may be wrong or biased.

**D-05 What the cockpit refuses:** (a) individual salaries or pay; the CFO said they "must never show up in anything
Ananya sees, only totals" (T2), and a CEO-facing tool is exactly that; (b) survey comments (every team is under 6,
so none can be anonymous, and whether she sees them is her open decision); (c) predictions about named people;
(d) forecasts with no source. It says what it *can* give instead.

**D-06 Worry ranking.** score = impact x urgency (my 1-5 judgements) x confidence factor (1.0/0.7/0.4) x share of
evidence visible. Judgement inputs are in one file and labelled as judgement. Close scores (3rd vs 4th) are shown as
"below the line", not hidden.

**D-07 Payroll amounts are restricted at the citation layer** (`View.describe` never prints them), not only in the UI,
so no handler can leak them by accident. Tested. Aggregates are allowed.

**D-08 No inferences about named individuals' wellbeing.** The leave register shows Priya Nair took five PM half-days
in September (including 15 Sep, the original Atlas GA date) and Deepa is worried about one unnamed engineer. A link is
tempting; I judged the evidence too thin and the harm of a wrong or exposed guess too high. The data stays in the
model; the cockpit reports team-level signals only. Revisit if Day 3 data (on-call rota, incidents) supports it.

**D-09 Don't merge entities silently.** 'Sapphire Events Pvt Ltd' and 'Saphire Event Mgmt' are probably one vendor, but
nothing proves it, and merging would hide a possible duplicate payment. Both are shown with the caveat.

**D-10 Raw sources are copied into the repo.** Synthetic data, no confidentiality issue, and reviewers can rebuild
from a fresh clone.

**D-11 No morning notification (T6a).** Nothing live to refresh from; we show data age instead. See `responses/T6a_response.md`.

**D-12 (planned) Agent memory** = append-only dated records read through `View`, so an agent's recall respects release dates.

---
## Added 20 Nov

**D-08 (revised).** T6d says Priya resigned, so the Priya facts became decision-relevant. Revision: the cockpit may state *work-concentration facts* about her (share of open points and commits, with caveats) and neutral dated records (the 1 Sep email, no reply in the data). It still draws no conclusion about why, and still does not use her leave. Alternative: say nothing about her work at all, which would fail the CEO's board-call question.

**D-12 (final) Agent memory.** Each agent reads dated records through `View`, so an agent cannot recall something its source has not released (tested: Sneha under `known_by` Day 2 says nothing of on-call). Alternative: an LLM with a long memory file, which could not guarantee that and cannot be tested offline. Cost: replies are template-assembled and shallow.

**D-13 Simulation lives in its own database.** `build/sim.db`, never joined to the evidence DB, so no answer can cite an invented event. Rates come from Sep-Oct history. Alternative: write synthetic rows into the main tables flagged `synthetic=1`; one forgotten WHERE clause would leak them.

**D-14 Refuse the "who will quit" ranking and Slack messages (T6c).** 19 people, no exit history, no Slack data; a ranking is a guess about named individuals whose wrong or leaked version causes real harm, and private messages are not the company's to read for this purpose. Offered instead: team-level signals and a work-concentration view. Alternative: a transparent scoring of leave and pulse; I judged it would be read as a prediction no matter how it was labelled. Open for the owner to overrule.

**D-15 Planned org changes are stored but inert.** `org_history` holds T6b's CRO move as a 'planned' row with no date and no manager; queries ignore it unless asked. Alternative: apply it from 1 Dec. That would invent a date and a person.

**D-16 Claims after the export are 'unverified', not 'false'.** T6d is shown with its source and with what the records can and cannot confirm. Confidence is capped at low for anything resting only on it.

**D-17 `evidence_later` in the worry list.** Evidence that did not exist on an earlier date adds to an item when released but its absence never lowers an earlier brief. Without this, the 17 Nov brief would change retroactively. Tested: the 17 Nov ranking is reproducible.

**D-18 Jira beats a call and beats board prose; a dated financial record beats an email's wording.** Same ladder as D-04, now with two worked examples (N-28, N-30).
