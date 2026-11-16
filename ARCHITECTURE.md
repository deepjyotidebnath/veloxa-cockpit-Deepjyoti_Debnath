# Architecture (Day 1 baseline; updated through Day 4)

## Goal
A compact, explainable CEO cockpit. Correctness, provenance and refusal behaviour take priority over fluent but ungrounded generation.

## Data flow
1. `data/raw/` stores the four release folders unchanged.
2. `src/ingest.py` extracts DOCX paragraphs/tables, XLSX sheet rows, PDF text, CSV, EML and TXT.
3. Each source becomes one JSONL evidence record: `id`, relative `source`, `release_date`, `text`.
4. `src/cockpit.py` applies a selected release cutoff and routes known question classes to concise answer templates with source citations, confidence and status.
5. `app.py` renders the cockpit, worry list, 14 colleague profiles and visible-source list.
6. `tests/` checks grounded answers, refusals, source cutoff and agent/risk invariants.

## Core entities
- **SourceRecord**: source file, release date, extracted text, immutable source path.
- **Person**: employee ID, name, role, team, grounded facts, history, explicitly labelled fictional-life assumption.
- **EvidenceRef**: source filename(s) cited by an answer or risk.
- **CockpitAnswer**: answer text, confidence, evidence refs, status (`answered`, `uncertain`, `unknown`, `refused`).
- **RiskItem**: rank, title, severity, rationale, evidence refs.

## Release-time model
Release dates are mapped from folder names: Day 1=2026-11-16, Day 2=2026-11-17, Day 3=2026-11-18, Day 4=2026-11-19. The UI cutoff controls which records are visible. A query dated before Day 4 must not use T6d. Source event dates and release dates are distinct.

## Trust and reconciliation
Structured exports and signed/dated documents are preferred for fields they directly record. Transcripts are treated as leads, not authoritative structured facts. A contradiction is not silently overwritten: see `TRANSCRIPT_NOTES.md`. The system does not infer the meaning of unclear amounts or misheard tool names.

## Agent design
Fourteen role profiles are deterministic and grounded in records. Their work facts/history cite the underlying data; personal-life details are deliberately fictional, marked as assumptions, and are not used to answer business questions. Agent simulation must not claim access to private thoughts, Slack or unrecorded activity.

## Deliberate simplifications
SQLite/vector DB and external LLM were not introduced in this five-day scope. A JSONL evidence index is portable and transparent. Q&A routing is deterministic to make confidence/refusal behaviour testable. This can later be replaced by hybrid retrieval + constrained generation without changing the source/evidence contract.
