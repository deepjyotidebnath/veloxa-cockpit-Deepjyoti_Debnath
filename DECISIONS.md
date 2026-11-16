# Defensible decisions

1. **JSONL evidence index instead of vector DB.** Small fixed release pack, easy audit, no infrastructure/API key, deterministic tests. Trade-off: limited semantic retrieval; add hybrid search if scope grows.
2. **Deterministic Q&A instead of unrestricted LLM.** Ensures reproducibility, source citations and explicit refusal. Trade-off: limited question coverage. Unknown questions say “I don't know”.
3. **Exports over transcript for structured facts.** HRIS, GL, Jira, board updates are preferred for fields they directly record; never treat any export as globally infallible.
4. **Release date and event date are separate.** A record is available only from its release folder date; prevents future leakage.
5. **Fourteen agents are profile simulations.** Their work facts are evidence-grounded. Personal-life detail is invented and explicitly marked; agents do not claim private thoughts or unsourced actions.
6. **No individual salary disclosure.** CFO explicitly requires totals only in CEO-facing output.
7. **No Slack/message disclosure.** No export supplied; T1's “slag channel” may be misheard. Never fabricate messages.
8. **No individual quit-risk scores.** Team-level engagement and confirmed notice facts are reportable; a person-level prediction is not supported by this data.
9. **Risk ranking is a transparent prioritisation, not probability.** Ranking reflects severity and evidence, not a statistical forecast.
10. **Priya resignation is a signal, not yet a reconciled HR fact.** Preserve Keka's 31-Oct status and cite the 19-Nov CEO note separately until confirmation arrives.
