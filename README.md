# Veloxa CXO Cockpit

Ask one question about a (fictional) 19-person company, with its 14 engineering/finance/people/marketing staff also available as interviewable agents and get a short answer that **cites the records behind it,
states a confidence level, and says "I don't know" or "the sources disagree" when that is the honest answer**.
Opening it with no question shows the top things to worry about, each backed by evidence.

Veloxa is a synthetic company created for the Hiyaku Systems hackathon; none of it is real.

## One command (from a fresh clone)

```bash
./run.sh
```

Builds the database from `data/`, runs every test, then prints the CEO's default "what to worry about" view.
Needs only Python 3.9+; no packages to install.

## Using it

```bash
python -m cockpit brief                      # top 3 worries (T6a: no question needed)
python -m cockpit brief --all                # every ranked item
python -m cockpit ask "What is our ARR?"
python -m cockpit ask "How much does Priya earn?"                 # refused, and says why
python -m cockpit ask "What is going on with Siddharth?" --known-by 2026-11-16   # Day 1 knowledge only
python -m cockpit sources                    # every source, release date, reliability
python -m cockpit ask "Who is a single point of failure?"
python -m cockpit ask "Pria resigned. What does this do to version three?"   # T6d: facts, no invented date
python -m cockpit ask "Rank everyone by who is likely to quit"              # refused, with reasons (T6c)
python -m cockpit agents                                                     # the 14 colleagues
python -m cockpit agent Sneha "How is on-call?"                              # interview one (add --known-by DATE)
python -m cockpit simulate --days 14 --seed 7                                # stretch: synthetic activity after 31 Oct
```

`--known-by DATE` = only sources released on/before DATE (no later material leaks in).
`--as-of DATE` = only facts effective on/before DATE.

## Tests

```bash
python -m unittest discover -s tests -v
```

- `tests/qa_cases.json`: 49 questions with expected status and required/forbidden text (31 are refusals,
  honest-uncertainty or point-in-time leakage checks, including Day-by-Day `known_by` cases). Readable without reading code.
- `tests/test_agents_org_sim.py`: 14 agents match the HR master and are logged as assumptions; agent memory respects release
  dates; a simulated re-org (T6b) breaks nothing; the simulation is seeded and obeys constraints from the data.
- `tests/test_raw_fidelity.py`: every CSV equals the original xlsx in `data/raw` (skipped if `openpyxl` is absent).
- `tests/test_integrity.py`: data cross-checks (e.g. GL salary line equals the register gross) and safety checks
  (no individual pay emitted, no citation from an unreleased source).

## Layout

| Path | What |
|---|---|
| `data/dayN/` | Sources as released, one folder per release day (`data/raw/` = the original xlsx/pdf/eml files) |
| `cockpit/db.py` | Loader: every record gets a source, `released_on` and `effective_date` |
| `cockpit/view.py` | Point-in-time filter + citation resolver |
| `cockpit/worry.py` | Ranked worry list |
| `cockpit/ask.py` | Question answering, refusals |
| `cockpit/eng.py` `cockpit/org.py` | Jira/git/on-call/incident metrics; effective-dated reporting lines |
| `cockpit/agents.py` `agents/profiles.json` | The 14 agents (facts from records, invented lives logged as A-16..A-29) |
| `cockpit/sim.py` | Stretch simulation, stored apart from the evidence database |
| `responses/` | Written replies to each CEO voice note |
| `ARCHITECTURE.md` `DECISIONS.md` `ASSUMPTIONS.md` `TRANSCRIPT_NOTES.md` `AI_LOG.md` | Required logs |

## Status (20 Nov)

Built: all four release days loaded; cockpit with citations, confidence and honest refusals; ranked worry view;
point-in-time (`--known-by`, `--as-of`); 14 agents; effective-dated org; seeded simulation; 49 QA cases + 28 test
functions; responses to T6a-T6d.

Known gaps: agents are rule-based, so their replies are short; the answer router is keyword-based and a new phrasing
falls through to "I don't know" (safe, but limiting); `TRANSCRIPT_NOTES.md` conclusions are AI-drafted proposals that
the owner must sign off; T6b-T6d responses were committed after their deadlines (see `AI_LOG.md`).
