"""The 14 colleagues as agents you can interview.  python -m cockpit agent "Sneha" "How is on-call?"

Design (DECISIONS D-12):
  * Facts come ONLY from the database through View, so an agent cannot remember what its source had not released.
  * Personality and private life come from agents/profiles.json and are INVENTED; every reply that uses them says so.
  * Rule-based (no LLM): replies are assembled from memory records, which keeps them consistent with the data.
  * Agents never disclose pay, survey comments, or speculate about colleagues' private lives or intentions.
"""
import json
import pathlib
import re
from .view import View, EXPORT_DATE
from . import eng

PROFILES = {p["emp_id"]: p for p in json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "agents" / "profiles.json").read_text())}


def find(v, who):
    who = who.lower()
    for eid, p in PROFILES.items():
        if who in p["name"].lower():
            return p
    return None


def memory(v, emp_id):
    """Dated records this person is party to, visible under v. Newest last."""
    d = v.db
    e = d.execute("select * from employees where emp_id=?", (emp_id,)).fetchone()
    out = [("employee", e["join_date"], f"joined as {e['title']} ({e['department']})", "employees:" + emp_id)]
    for r in v.rows("leave", "emp_id=?", (emp_id,), "from_date"):
        out.append(("leave", r["from_date"], f"{r['leave_type']} leave, {r['days']} day(s)", "leave:" + r["leave_id"]))
    for r in v.rows("emails", "sender like ? or recipient like ?", (f"%{e['work_email']}%",) * 2, "effective_date"):
        who = "sent" if e["work_email"] in r["sender"] else "received"
        out.append(("email", r["effective_date"], f"{who} email '{r['subject']}'", "emails:" + r["email_id"]))
    if v.source_visible("SRC-PD"):
        for r in v.db.execute("select * from incidents where responder_emp_id=? order by opened_utc", (emp_id,)):
            if not v.as_of or r["effective_date"] <= v.as_of:
                out.append(("incident", r["effective_date"], f"responded to {r['severity']} {r['id']} on {r['service']}",
                            "incidents:" + r["id"]))
    return sorted(out, key=lambda x: x[1] or "")


def _status(v, emp_id):
    d = v.as_of or EXPORT_DATE
    e = v.db.execute("select * from employees where emp_id=?", (emp_id,)).fetchone()
    return e, bool(e["exit_date"] and e["exit_date"] < d)


def reply(v, who, question):
    p = find(v, who)
    if not p:
        return f"No colleague matches '{who}'. The 14: " + ", ".join(x["name"] for x in PROFILES.values())
    eid, q = p["emp_id"], question.lower()
    e, left = _status(v, eid)
    first = p["name"].split()[0]
    mem = memory(v, eid)
    pl = p["personal_life"]
    foot = "\n  [facts from records: " + ", ".join(sorted({m[3] for m in mem[-3:]})) + "]" if mem else ""
    persona = f"\n  [persona invented, see {p['assumption_id']}]"
    if re.search(r"salary|pay\b|paid|earn|ctc|how much do you make", q):
        return f"{first}: That's not something I'll share, and it shouldn't be sitting in a tool the CEO opens."
    if re.search(r"comment|survey|pulse", q):
        return f"{first}: I answered the survey; I'm not going to repeat what anyone wrote, mine or anyone's."
    if re.search(r"(is|will|about) (\w+ )?(going to |gonna )?(quit|resign|leav)|who.*(quit|leav)", q) and first.lower() not in q:
        return f"{first}: I won't speculate about colleagues' plans. Ask them, or ask Deepa."
    if re.search(r"\b(family|live|home|weekends?|hobbys?|hobbies|outside work|free time|personal)\b", q):
        return f"{first}: {pl['home']}. Outside work: {pl['outside']}." + persona
    if re.search(r"worr|stress|frustrat|honest|really feel|burn", q):
        return f"{first}: ({p['voice']}) {pl['worry']}." + persona + foot
    if left and re.search(r"now|currently|this week", q):
        return f"{first}: I left on {e['exit_date']}. I can tell you what I handed over, not what's happening now." + foot
    if re.search(r"resign|notice|leaving|quit", q) and eid == "VX007":
        return (f"{first}: I'm not going to talk about that here. If something has been announced, it's for Ananya and "
                "Vikram to say.") + persona
    if re.search(r"work|doing|workload|busy|on call|on-call|ticket|atlas|project|role", q):
        return f"{first}: " + _work(v, eid, e) + foot
    if re.search(r"history|how long|joined|background|tenure", q):
        return f"{first}: I joined on {e['join_date']} as {e['title']}. " + "; ".join(
            f"{m[1]}: {m[2]}" for m in mem[1:6]) + foot
    return f"{first}: I don't know about that, or it isn't mine to answer. Ask me about my work, my history, or how I'm doing." + foot


def _work(v, eid, e):
    bits = [f"I'm {e['title']} in {e['department']}."]
    j = eng.jira_open(v)
    if j and eid in j["by_emp"]:
        o = j["by_emp"][eid]
        bits.append(f"In Atlas I hold {o['open_issues']} open tickets ({o['open_points']} of {j['open_points']} open points).")
    oc = eng.oncall_load(v)
    if oc and eid == "VX012":
        bits.append(f"I was on the on-call rota in {oc['sneha_primary'] + oc['sneha_secondary']} of {oc['weeks']} weeks.")
    cp = eng.commit_profile(v, eid) if eid in ("VX004", "VX007", "VX009", "VX012", "VX018") else None
    if cp:
        bits.append(f"{cp['n']} commits in the log.")
    if eid == "VX014":
        bits.append("I run accounts and payroll; in Feb I was on leave and Karthik ran the payroll.")
    if eid == "VX015" and v.source_visible("SRC-HIRE"):
        bits.append("My two backend requisitions (REQ-014/015) are on hold.")
    if eid == "VX013" and v.source_visible("SRC-LAUNCH"):
        bits.append("I own the Atlas launch kit: ready since July, waiting on a date.")
    return " ".join(bits)
