# AI log

Tool: Claude (Claude Code session). It read the Drive folders, wrote the loader, answer engine, tests and a first draft
of every document. **The owner is responsible for all of it** and must be able to explain and change any line without AI.

## Tasks given to AI
| When | Task |
|---|---|
| 16 Nov | Read the Day 1 pack from Drive (brief, T1, T2, master, GL, payroll, boards, 3 emails, templates); list conflicts |
| 20 Nov | Read the Day 3 and Day 4 material from Drive (Jira, git log, PagerDuty, rota, launch kit, invoice, T4/T5/T6b-d); extend loader, answers, worry list; build 14 agents, simulation, 19 new QA cases and 17 tests; draft T6b-T6d responses and all log additions |
| 17 Nov | Read the Day 2 pack (T3, T6a, leave, hiring, pulse, resignation, 4 emails); build loader, cockpit, worry view, 41 tests; draft T6a response and all logs |

## Where the AI was wrong, and what changed
1. **Routing bug (caught in my own review before running).** "Which engineer is Deepa worried about?" matched the generic
   *worry* rule and would have returned the ranked list instead of "I don't know". Reordered rules; test U01 guards it.
2. **Future leak (caught in review).** The attrition answer quoted the Day 2 call and pulse survey even when only Day 1
   was released. Each clause is now gated on its own source; tests T02/T03 guard it.
3. **Wrong fact in a caveat.** I first wrote that the tracker "never had more than 3 open". Querying it: 4 counting
   on-hold reqs, at most 1 in April. Text corrected to what the data shows.
4. **Too-harsh confidence rule.** One hidden evidence record dropped an item straight to "low". Now one level down.
5. **Four test failures on the first run.** Worry answers listed evidence in text but not in `cites`; a "0 open roles"
   answer cited nothing; one test had wrong casing. Fixed the code (not the tests), except the casing.
6. **Excerpt bug.** Transcript citations showed the paragraph start, not the matched phrase. Now a window around the match.
7. **Process error.** An earlier turn of the session said the Day 1 work was starting while only raw CSVs had been
   written; Day 1's loader, docs and commits did not exist until today. ARCHITECTURE.md therefore missed its Mon 16 Nov
   deadline; this is also visible in the commit dates (not backdated).

## Limits the owner should verify
- **Source fidelity.** All xlsx/pdf/docx files were read through Drive's *text rendering*, not the original bytes;
  payroll rows were expanded from one per-person table because every month was identical in that rendering. Re-check
  `data/day1/payroll_jan_mar_2026.csv` and the two other xlsx-derived CSVs against the originals.
- **Conflict reasoning is a draft.** `TRANSCRIPT_NOTES.md` conclusions are AI proposals with sign-off boxes. The rules say
  AI must not decide which source is true for you: read each, then tick or overrule.
- **Impact/urgency scores** in `worry.py` are the AI's judgement calls (D-06).
- **No GitHub push** was possible from this environment; the repo link and the Mon-night email are for you to do.

## Added 20 Nov
**More errors by the AI, and what changed**
8. **Lateness, stated plainly.** Day 3 and Day 4 work, and the T6b/T6c/T6d responses, were not done on their release days. They are committed on 20 Nov; the commit dates are true, not backdated.
9. **Backspace bug.** A regex `\b` inside a non-raw Python string became a backspace character, so "who reports to the CRO?" silently failed. Found by running my own sample questions, fixed, and a QA case (U11) now covers it.
10. **Wrong router order.** "When will Atlas ship?" hit the generic forecast rule ("will") and said "I don't know" even though Jira has a date. Added an Atlas-specific rule before it.
11. **A test that proved the wrong thing.** U03 ("When is Atlas going to launch?") expected "unknown" with all data loaded; true only on Day 2. I pinned it to Day 2 knowledge and added the full-data version (Q31) rather than loosening the assertion.
12. **Retroactive brief change (caught before shipping).** Adding Day 3 evidence to old items would have lowered the 17 Nov brief's scores. Fixed with `evidence_later` and a test that the 17 Nov ranking is reproducible.
13. **Context loss.** Partway through, my working context was reset and I rediscovered earlier work (the repo, an unfinished `agents.py`) from the filesystem and git history rather than from memory. I re-ran the tests before building on it.
14. **Planned-row priority.** `include_planned=True` returned the recorded manager because ordering put it first; test caught it.

**Verified against the originals this time.** The earlier CSVs were built from Drive's text rendering. I downloaded the original xlsx files and checked them row by row (`tests/test_raw_fidelity.py`). They match.

**Limits the owner should verify**
- Every invented personal life (A-16..A-29) is mine; read them and keep, change or cut.
- `TRANSCRIPT_NOTES.md` N-25..N-38 conclusions are proposals; the rules say you decide which source is true.
- The refusal of T6c (D-14) is my judgement; you may disagree.
- No push to GitHub was possible (the token in this environment is invalid): you must create the public repo, push, and send the two emails yourself.
