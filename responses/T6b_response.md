# Response to T6b (CEO voice note, released Wed 18 Nov)

> "Marketing will report to the new CRO from next month. Or the month after, still finalising. Make sure the thing doesn't break when we move people around."

*Process note: this was due Wed 18 Nov, 11:59 PM IST and is committed on Fri 20 Nov. The commit date shows it. See AI_LOG.md.*

**Decision: change made (the system now survives re-orgs), with one pushback (I did not apply the move).**

## What changed
- Reporting lines are now **effective-dated**: `org_history` (emp, manager, from, to, status) read through `cockpit/org.py`. Nothing in the answer layer assumes who reports to whom.
- A re-org is now a data change, not a code change. `tests/test_agents_org_sim.py::Reorg` inserts a CRO, moves Marketing under them from 1 Dec in a scratch copy of the database, then checks: reporting lines before and after the date, the management chain, every question type and the worry list still run, and no planned row leaks into answers.
- "Who does Nikhil report to?" answers from the HR master and says a move is planned but unconfirmed. "Who reports to the CRO?" answers "I don't know": there is no CRO in the records.

## Where I'm pushing back
1. **I did not apply "from next month".** Three facts are missing: the person (no CRO in the HR master), the date ("next month, or the month after, still finalising"), and any dated record. Nikhil's own version is "I hear" (T4). The move is stored as a *planned* row with no date and no manager, and the cockpit ignores it until a dated record exists. Applying it from 1 Dec would be inventing a fact in a tool whose job is to separate facts from claims.
2. **"Doesn't break" is only as good as what I tested.** I tested reporting lines, chains and every answer type. I did not test things that don't exist yet: budgets by reporting line, pulse by manager, access rules by hierarchy.
3. **Team-level data does not move with the people automatically.** Pulse and requisitions are keyed by team, not manager. If Marketing moves under the CRO the team is still "Marketing", which is probably right. If you wanted views by reporting line, that needs a decision from you.

## Not done
No CRO persona. An invented executive would add a fictional person to a model whose point is real records.
