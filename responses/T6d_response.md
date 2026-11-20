# Response to T6d (CEO voice note, released Thu 19 Nov)

> "Bad news, Pria resigned this morning. Notice period two months, I think. What does this do to version three? I need to know before the board call."

*Process note: due Thu 19 Nov, 11:59 PM IST; committed Fri 20 Nov.*

**Decision: change made (new answer), with a pushback: I will not give you a date for v3.**

## What the cockpit now says (`ask "Pria resigned. What does this do to version three?"`)
- **The news itself:** it comes only from your voice note (undated, "this morning"). "Pria" is Priya Nair, the only Priya. The HR export is dated 31 Oct and shows her Active, so no system record confirms it. That is expected, and the answer says so.
- **Exposure, from the records:** Priya holds 62 of 115 open Atlas story points (54%), all of re-routing (the headline feature, 13 of 42 points done), most of core engine and hardening, and 70% of atlas-engine commits across her two git identities. The April plan gave the work to four people; the tickets give much of it to one.
- **Timing, as arithmetic only:** if two months starts 19 Nov, her last day is about 19 Jan 2027, after the 15 Dec date in Jira. But "two months, I think" is a recollection, and Siddharth's notice (15 Sep to 31 Oct) was 46 days, so notice here is not fixed.
- **The brief:** `python -m cockpit brief` now ranks this second, after Atlas itself.

## Pushbacks
1. **No v3 date.** Nothing in the data tells me how documented her work is, who can take re-routing, or whether she stays through GA. Any date would be invented, and you would repeat it to your board. I'd rather give you the exposure and three questions for Vikram: *who takes re-routing, what 'done' means for 15 Dec, what is documented*.
2. **The board may already have a wrong picture.** Board Q3 (6 Oct) calls the engine "feature-complete". Jira has re-routing at 13 of 42 points and nothing resolved since 17 Sep; Vikram's call says "on track" for a September board date although he moved GA to 15 Dec himself on 2 Sep. Before the call, you probably want these reconciled more than you want the resignation analysed. Believed: Jira over both (TRANSCRIPT_NOTES N-28, N-29).
3. **I did not connect her resignation to her leave, her late-night commits, or her 1 Sep "Atlas ownership" email.** The email exists, with no reply in the data; the cockpit shows it as a dated fact and says it doesn't know what it was about. A story that fits is not evidence (DECISIONS D-08, revised).
4. **I did not answer "why".** `ask "Why did Priya resign?"` returns "I don't know".

## Not done
No retention plan, no replacement suggestion, no revised schedule. These need decisions the records can't make.
