# AI use log

| Date | Task | AI contribution | Human review / correction |
|---|---|---|---|
| 2026-11-16 | Initial architecture and source review | Suggested evidence-first architecture, release-date gating, deterministic Q&A and risk prioritisation. | Kept scope small and reproducible; did not add an external LLM or vector DB. |
| 2026-11-16 | Transcript conflict review | Suggested likely mappings: Jeera→Jira, Kayka→Keka, Joho→Zoho, Pria→Priya, Ayesha→Aisha. | Marked mappings as confidence-qualified; did not treat uncertain spellings as proven. |
| 2026-11-16 | Employee agents | Drafted profile summaries and fictional personal-life details. | Work facts are tied to supplied records; personal details explicitly labelled assumptions and excluded from business answers. |
| 2026-11-16 | Voice-note decisions | Drafted responses for T6a–T6d. | T6b deferred pending CRO/date; T6c refused private messages and quit rankings; T6d kept resignation unverified. |
| 2026-11-16 | Code generation | Generated initial deterministic Streamlit app and test suite. | Must run `pytest -q` locally and manually review before submission; no claim of external deployment or GitHub push. |

## Corrections made during review
- An early interpretation treated T1's auto-transcribed “one-eighty” as a reliable 180-person headcount. This was rejected after checking the 31-Oct Keka export (19 employee rows) and both board updates (team 19). The transcript wording remains logged as a conflict; it is not silently rewritten.
- An early Day 2 worry-list draft included marketing/engineering operational evidence released on Day 3. The date-scoped risk list and tests were corrected so later release packs cannot leak into earlier answers.
- An early Atlas answer included T6d's Priya resignation signal even for a Day 3 cutoff. This was corrected; a regression test now checks Day 3 versus Day 4 answers separately.
