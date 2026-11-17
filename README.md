# Veloxa CXO Cockpit

Ask one question about a (fictional) 19-person company and get a short answer that **cites the records behind it,
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
```

`--known-by DATE` = only sources released on/before DATE (no later material leaks in).
`--as-of DATE` = only facts effective on/before DATE.

## Tests

```bash
python -m unittest discover -s tests -v
```

- `tests/qa_cases.json`: 30 questions with expected status and required/forbidden text (17 are refusals,
  honest-uncertainty or point-in-time leakage checks). Readable without reading code.
- `tests/test_integrity.py`: data cross-checks (e.g. GL salary line equals the register gross) and safety checks
  (no individual pay emitted, no citation from an unreleased source).

## Layout

| Path | What |
|---|---|
| `data/dayN/` | Raw sources exactly as released, one folder per release day |
| `cockpit/db.py` | Loader: every record gets a source, `released_on` and `effective_date` |
| `cockpit/view.py` | Point-in-time filter + citation resolver |
| `cockpit/worry.py` | Ranked worry list |
| `cockpit/ask.py` | Question answering, refusals |
| `responses/` | Written replies to each CEO voice note |
| `ARCHITECTURE.md` `DECISIONS.md` `ASSUMPTIONS.md` `TRANSCRIPT_NOTES.md` `AI_LOG.md` | Required logs |

## Status

Built: Day 1 + Day 2 data, cockpit, worry view, tests, T6a response.
Not yet built: the 14 AI-agent colleagues, Day 3/4 data, stretch (agents generating activity after 31 Oct).
