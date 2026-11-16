# Veloxa CXO Cockpit

Evidence-first executive cockpit for the fictional Veloxa Technologies hackathon scenario. It loads the four supplied release packs, preserves raw records, creates a searchable evidence index, presents 14 grounded colleague profiles, ranks evidence-backed risks, supports date-scoped views, and refuses unsupported/private requests.

## One-command fresh setup and run

From the repository root (Python 3.10+), run this single cross-platform command:

```bash
python run.py
```

It installs dependencies, rebuilds the evidence index and launches Streamlit. Open the local URL printed by Streamlit. The app is deterministic and does not require an API key or external LLM. This is intentional: the demo remains reproducible and every answer path can be explained. Agent interviews are profile-based simulations, not free-form claims about private thoughts.

## Tests

```bash
python -m pytest -q
```

The suite includes 25 expected-answer question cases plus refusal/uncertainty cases, agent integrity, risk evidence and point-in-time checks (60 tests currently pass).

## Data and privacy

All supplied files are retained under `data/raw/`. `python -m src.ingest` extracts supported DOCX, XLSX, PDF, CSV, EML and TXT sources into `data/processed/evidence.jsonl`. The raw files remain authoritative; derived text is reproducible. Do not expose individual salary rows or private messages. The supplied materials do not include Slack exports.

## Current scope and limitations

- Evidence index: all readable files in all four release folders.
- Fourteen profiles: five Engineering, three Finance, three HR/People and three Marketing.
- Q&A uses auditable question routing and fixed evidence-backed answer templates, not a generative model. Unsupported questions return `I don't know`.
- Point-in-time selector gates source visibility by release date. Facts with explicit historical dates are still reported as those facts, not rewritten as current status.
- Risk ranking is an initial human-authored prioritisation, not a statistical prediction.
- No production authentication, role-based access control, external integrations or live Slack connector is included.
