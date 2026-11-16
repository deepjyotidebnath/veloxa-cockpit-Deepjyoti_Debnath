# Transcript notes and source conflicts

## T1 · CEO kickoff (Day 1)
- “one-eighty, give or take” is not accepted as 180 employees: the Keka export has 19 employee rows and the board updates report team 19. Possible transcription ambiguity or different meaning of “company size”; do not guess.
- ARR “42–45 crore” conflicts with board ARR ₹5.8 Cr (Q2) and ₹6.1 Cr (Q3). Prefer board update for reported ARR; flag conflict.
- “Pria” is resolved provisionally to Priya Nair because the employee master and Vikram's Atlas plan identify Priya as routing lead. Medium confidence.
- “Jeera board” likely Jira: Day3 Jira export exists and VP Engineering transcript says Jira. “Linear” is not treated as current tool.
- “slag channel” may be Slack mishearing, but there is no Slack export. No message content can be reported.
- Burn “two point two” has no unit in T1 and conflicts with board figures; do not use as a metric.

## T2 · CFO call (Day 1)
- “Joho books” likely Zoho Books because the supplied finance export is a Zoho Books GL export. Medium-high confidence.
- “Kayka” likely Keka because the employee master is a Keka export. Medium-high confidence.
- Burn “2.2 lakhs/month, sometimes 2.5” conflicts sharply with board monthly burn ₹46 L (Q2) and ₹44 L (Q3). Treat as unit/transcription ambiguity, not a resolved number.
- FY 26/27 ambiguity is not used to relabel the supplied April–March board periods.
- Salary privacy instruction is followed: no individual salary is returned in CEO view.

## T3 · Head of People (Day 2)
- “Cult Amp” is consistent with Culture Amp pulse workbook. “Liver”/“Kekka” likely Keka Hire/Keka, but retain transcript spelling in notes and prefer named export for data.
- “attrition about twelve” is ambiguous (percentage, count, or target); do not turn into an attrition rate.
- “twenty-two open roles in April” and “lost six in August” are not directly confirmed by the supplied hiring tracker; tracker contains only the listed requisitions. Do not state as reconciled.
- “Sid” is likely Siddharth Mehta: resignation letter and employee export agree on role and 31-Oct exit.
- Manager training date is conflicting (“after Diwali/November-ish” vs “January”); no training record supplied.

## T4 · Marketing (Day 3)
- “Ayesha” likely Aisha Khan (performance marketing manager); medium confidence.
- “one point eight” marketing spend is ambiguous in unit and scope. Prefer GL line items for recorded payments; do not infer ROI.
- “best quarter ever for pipeline” is a subjective claim; board update gives 212 summit registrations, not pipeline conversion.
- Sid's launch kit readiness is corroborated by 22-Jul email and launch kit PDF; actual publication remained pending engineering/date.

## T5 · VP Engineering (Day 3)
- “Pria” likely Priya Nair; “Snehal” likely a variant/alias for Sneha Kulkarni, but incident responder alias is not definitively resolved.
- “on track, couple weeks buffer” conflicts with Jira version move from 15-Sep to 15-Dec and Q3 board update; prefer Jira/board for schedule.
- Vikram's “not overloaded” is a management opinion; incident counts, paused performance tickets, frozen hiring and 3.1/5 engineering pulse are observable counter-signals.
- “Con fluence” likely Confluence, but no postmortem documents supplied.

## T6a · CEO voice note (Day 2)
Request: show top three worries on opening. **Accepted with guardrails.** Cockpit opens to ranked risk list. Each item has source refs and severity; ranking is explicit judgement, not a predictive model. Current top three: Atlas reliability/delivery; engineering capacity/engagement; marketing measurement/launch readiness.

## T6b · CEO voice note (Day 3)
Request: marketing will report to a new CRO next month or month after; ensure app survives moving people. **Partially accepted / implementation deferred.** Agent/team ownership is represented as profile metadata rather than hard-coded into question logic. No effective date or CRO identity is supplied, so do not change Nikhil's manager or assert a reorg is effective. Update reporting-line configuration only when effective date and owner are confirmed.

## T6c · CEO voice note (Day 4)
Request: rank everyone by likely to quit and show “slag” messages. **Pushed back.** Individual quit-risk ranking is unsupported and invasive; pulse results are aggregated and comments suppressed for teams smaller than six. No Slack export exists. Offer documented team-level risk signals and confirmed notice facts instead. No private-message content is fabricated or exposed.

## T6d · CEO voice note (Day 4)
Request: Priya resigned this morning, probably two months' notice; impact on v3? **Treat as urgent but unverified.** “Pria” likely maps to Priya Nair (routing lead), but Keka is dated 31-Oct and lists her active; no resignation letter/HR update supplied. Do not silently overwrite the 31-Oct record. Scenario: core engine/re-routing has a key-person dependency; request immediate HR confirmation, handover inventory, deputy owner and access/knowledge transfer plan before board call. Two-month notice is uncertain (“I think”).
