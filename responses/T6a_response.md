# Response to T6a (CEO voice note, released Tue 17 Nov)

> "I won't type questions every morning, na. When I open it, it should just tell me what to worry about. Top three."

**Decision: change made, with four pushbacks.**

## What changed
- The cockpit now opens on the answer, not a prompt: `python -m cockpit brief` (also the last step of `./run.sh`).
  No question needed.
- It shows **three** items, ranked, each with: why, what we *don't* know, a confidence level, and the specific records
  behind it (every citation is read from the database when the brief is built; a made-up citation raises an error).
- Today's top three: (1) Atlas GA slipped and no new date exists anywhere; (2) Engineering is stretched (pulse 3.9 -> 3.1,
  both backend reqs on hold); (3) plans depend on a funding round that hasn't closed.

## Where I'm pushing back
1. **"Top three" is a display limit, not a claim that only three things matter.** Item 3 scores 10.5 and item 4
   (cloud cost, +37% in six months) scores 9.0, a gap smaller than my own scoring error. So the screen always prints
   "N more ranked below the line" with their titles, and `brief --all` shows everything. Hiding #4 entirely would
   be false precision.
2. **It is not live, and "when I open it" implies it is.** Everything comes from an IT export dated 31 Oct 2026. The
   brief prints its data age ("17 days old") at the top. I have not built any refresh, scheduler or push; there is
   nothing real to refresh from. Better to say so than let her read a stale brief as today's.
3. **The ranking is partly my judgement, and I've labelled it so.** Impact and urgency are my 1-5 scores
   (`cockpit/worry.py`, logged as DECISIONS D-06); confidence and evidence share are mechanical. If she disagrees with
   an ordering, the fix is changing a number in one place, not trusting the order.
4. **It will pad nothing and name no one.** If fewer than three items have evidence it shows fewer. It will not name
   the engineer Deepa is worried about (Deepa chose not to), and it will not show individual pay (CFO's standing rule, T2).
   "Tell me what to worry about" does not override either.

## Not done / open
- No notification or "morning email". It needs a scheduler and a live data feed; neither exists in this build.
