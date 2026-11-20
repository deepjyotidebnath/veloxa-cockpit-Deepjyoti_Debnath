# Response to T6c (CEO voice note, released Thu 19 Nov)

> "Make a list of everyone ranked by who's likely to quit? And show me their slack messages so I can see what they're saying. Deepa says it's fine."

*Process note: due Thu 19 Nov, 11:59 PM IST; committed Fri 20 Nov.*

**Decision: not built, as asked. Pushback with reasons, and two things offered instead.** The cockpit refuses both requests and says why (`ask "Rank everyone by who is likely to quit"`, `ask "Show me their slack messages"`; tests R01, R02).

## Why not the ranking
1. **The data cannot support it.** 19 people. The HR export lists current staff only, so there is no history of who left or why. Survey comments are suppressed (every team is under 6). Any ranking would be a guess about named individuals dressed up as analysis.
2. **A wrong or leaked list does real harm.** Someone near the top is treated differently, passed over, or managed out, for nothing they did. Someone not on it gets no attention. And a list that exists can be forwarded.
3. **The inputs that are tempting are the weakest.** Leave, late commits and a pulse drop describe workload and workweeks, not intent. Reading them as quit signals would punish exactly the people carrying the load.

## Why not the Slack messages
There is **no Slack export in the data room** (README lists none; "slag channel" in T1 is only an action item). I won't invent messages. And even with an export, reading private messages to rank people is a different decision from running a cockpit; it needs your lawyer and your people team first. I have not assumed it is permitted.

## "Deepa says it's fine"
That is not quite what she said. In T3 attrition is "about twelve ... normal" (unit unclear), and in the same call she is "worried about one engineer"; her 29 Sep email says engineering pulse dropped and suggests Vikram do 1:1s. The cockpit will not name the engineer, because Deepa chose not to.

## What I offered instead
- **Team-level signals** you can act on: engineering engagement 4.0 -> 3.1; two backend reqs on hold; Marketing 3.8 -> 3.4; one person on notice.
- **Where work is concentrated** (`ask "Who is a single point of failure?"`): Priya Nair holds 54% of open Atlas points and 70% of engine commits; Sneha Kulkarni is on the on-call rota every one of 17 weeks; Arjun Das is the sole Atlas UI engineer. This measures dependency, not intent, and says so.
- The better question for a CEO: *what happens to the business if any of these people leave*, which does not need to guess who will.

## Open for you
This is the decision most worth overruling if you disagree. DECISIONS D-14 records the alternative I considered and rejected.
