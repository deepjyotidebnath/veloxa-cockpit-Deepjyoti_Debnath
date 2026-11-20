"""Point-in-time view over the database + citation resolver.

View(known_by, as_of):
  known_by -> only sources released on/before this date are visible (no leakage of later packs)
  as_of    -> only facts effective on/before this date are visible
Both optional; omit for "everything we have".
"""
import re
from . import db as dbm

EXPORT_DATE = "2026-10-31"  # IT export date for every data-room table


def inr(n):
    """Indian digit grouping: 1003000 -> Rs 10,03,000."""
    s = str(int(n))
    if len(s) <= 3:
        return f"Rs {s}"
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "Rs " + ",".join(parts + [tail])


class View:
    def __init__(self, known_by=None, as_of=None, db=None):
        self.db = db or dbm.connect()
        self.known_by, self.as_of = known_by, as_of

    # -- visibility -------------------------------------------------------
    def source_visible(self, source_id):
        if self.known_by is None:
            return True
        r = self.db.execute("select released_on from sources where source_id=?", (source_id,)).fetchone()
        return bool(r) and r["released_on"] <= self.known_by

    def rows(self, table, where="1", params=(), date_col=None):
        sql = f"select * from {table} where ({where})"
        args = list(params)
        if self.known_by is not None:
            sql += " and source_id in (select source_id from sources where released_on<=?)"
            args.append(self.known_by)
        if self.as_of is not None and date_col:
            sql += f" and ({date_col} is null or {date_col}<=?)"
            args.append(self.as_of)
        return self.db.execute(sql, args).fetchall()

    def employees_on(self, date=None):
        """Employees employed on `date` (default: the export date)."""
        d = date or self.as_of or EXPORT_DATE
        return self.rows("employees", "join_date<=? and (exit_date is null or exit_date>=?)", (d, d))

    # -- citations --------------------------------------------------------
    def describe(self, ref):
        """Turn 'table:key[|substring]' into a one-line fact read straight from the record.
        Raises KeyError if the record or excerpt does not exist, so a made-up citation fails loudly."""
        ref, _, needle = ref.partition("|")
        table, _, key = ref.partition(":")
        db = self.db
        if table == "employees":
            r = db.execute("select * from employees where emp_id=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            ex = f"; exit {r['exit_date']}" if r["exit_date"] else ""
            return (f"{r['emp_id']} {r['full_name']}, {r['title']} ({r['department']}); "
                    f"status {r['status']}; joined {r['join_date']}{ex}")
        if table == "gl":
            r = db.execute("select * from gl where voucher=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return (f"{r['voucher']} {r['effective_date']} {r['vendor']} {inr(r['amount_inr'])} "
                    f"[{r['cost_centre']}] \"{r['narration']}\"")
        if table == "payroll":  # restricted: never emit individual amounts (DECISIONS D-07)
            emp, month = key.split(":")
            r = db.execute("select p.*, e.join_date, e.full_name from payroll p join employees e using(emp_id) "
                           "where emp_id=? and month=?", (emp, month)).fetchone()
            if not r:
                raise KeyError(ref)
            return (f"payroll {month} {r['full_name']}: days payable {r['days_payable']} of "
                    f"{r['days_in_month']} (joined {r['join_date']}); amounts withheld")
        if table == "reqs":
            r = db.execute("select * from reqs where req_id=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return (f"{r['req_id']} {r['role']} ({r['team']}): {r['status']} since {r['status_date']}, "
                    f"{r['in_pipeline']} in pipeline" + (f"; {r['notes']}" if r["notes"] else ""))
        if table == "pulse":
            team, q = key.split(":")
            r = db.execute("select * from pulse where team=? and quarter=?", (team, q)).fetchone()
            if not r:
                raise KeyError(ref)
            return f"pulse {team} {q}: engagement {r['engagement']}/5, {r['responses']} of {r['team_size']} responded"
        if table == "leave":
            r = db.execute("select * from leave where leave_id=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return f"{r['leave_id']} {r['emp_id']} {r['leave_type']} {r['from_date']}..{r['to_date']} ({r['days']}d)"
        if table == "emails":
            r = db.execute("select * from emails where email_id=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            line = next((l for l in r["body"].splitlines() if l.strip() and needle in l), None) if needle else \
                next((l for l in r["body"].splitlines()[1:] if l.strip()), r["body"])
            if needle and not line:
                raise KeyError(ref)
            return f"email {r['effective_date']} {r['sender']} -> {r['recipient']} \"{r['subject']}\": {line.strip()}"
        if table in ("documents", "transcripts"):
            col, idc = ("documents", "doc_id") if table == "documents" else ("transcripts", "t_id")
            r = db.execute(f"select * from {col} where {idc}=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            line = next((l for l in r["body"].splitlines() if needle and re.search(re.escape(needle), l, re.I)), None) \
                if needle else r["body"].splitlines()[0]
            if not line:
                raise KeyError(ref)
            label = r["title"] if table == "documents" else r["t_id"]
            line = line.strip()
            if len(line) > 240 and needle:  # window around the matched phrase, not the paragraph start
                i = re.search(re.escape(needle), line, re.I).start()
                a, b = max(0, i - 90), min(len(line), i + 150)
                line = ("..." if a else "") + line[a:b].strip() + ("..." if b < len(line) else "")
            return f"{label}: {line[:260]}"
        if table == "jira":
            r = db.execute("select j.*, e.full_name from jira_issues j join employees e using(emp_id) where key=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            done = f", resolved {r['resolved']}" if r["resolved"] else ""
            return (f"{r['key']} \"{r['summary']}\" [{r['epic_name']}] {r['full_name']}, {r['story_points']} pts, "
                    f"{r['status']}, created {r['created']}{done}")
        if table == "versions":
            r = db.execute("select * from jira_versions where version=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return (f"Jira version '{r['version']}': release date {r['release_date']} (originally "
                    f"{r['original_release_date']}), last changed {r['last_changed']} by {r['changed_by']}")
        if table == "incidents":
            r = db.execute("select * from incidents where id=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return (f"{r['id']} {r['severity']} {r['service']} opened {r['opened_utc']} (UTC), "
                    f"{r['duration_min']} min, responder '{r['responder_as_written']}'")
        if table == "oncall":
            r = db.execute("select * from oncall where week_of=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return f"on-call week of {r['week_of']}: primary {r['primary_as_written']}, secondary {r['secondary_as_written']}"
        if table == "invoices":
            r = db.execute("select * from invoices where inv_no=?", (key,)).fetchone()
            if not r:
                raise KeyError(ref)
            return (f"invoice {r['inv_no']} {r['vendor']} dated {r['invoice_date']} for {r['period']}: "
                    f"{inr(r['total_inr'])} incl. GST")
        if table == "commits":  # aggregate over one person (both git identities for Priya)
            r = db.execute("select count(*) n, min(effective_date) a, max(effective_date) b, "
                           "sum(ist_hour>=22 or ist_hour<2) late, count(distinct author_email) ids "
                           "from commits where emp_id=?", (key,)).fetchone()
            if not r["n"]:
                raise KeyError(ref)
            return (f"git: {key} {r['n']} commits {r['a']}..{r['b']} under {r['ids']} author email(s); "
                    f"{round(100 * r['late'] / r['n'])}% between 22:00 and 02:00 IST")
        if table == "org":
            r = db.execute("select * from org_history where emp_id=? and status=?", tuple(key.split(":"))).fetchone()
            if not r:
                raise KeyError(ref)
            return f"org_history {r['emp_id']} -> {r['manager_id']} ({r['status']}; from {r['from_date']})"
        raise KeyError(ref)

    def ref_source(self, ref):
        table, _, key = ref.partition("|")[0].partition(":")
        db = self.db
        if table == "payroll":
            return "SRC-PAY"
        qmap = {"employees": ("employees", "emp_id"), "gl": ("gl", "voucher"), "reqs": ("reqs", "req_id"),
                "leave": ("leave", "leave_id"), "emails": ("emails", "email_id"),
                "documents": ("documents", "doc_id"), "transcripts": ("transcripts", "t_id")}
        if table == "pulse":
            return "SRC-PULSE"
        fixed = {"jira": "SRC-JIRA", "versions": "SRC-JIRA", "incidents": "SRC-PD", "oncall": "SRC-ROTA",
                 "commits": "SRC-GIT", "invoices": "SRC-INV-PIS114", "org": "SRC-T6b"}
        if table in fixed:
            return fixed[table]
        t, idc = qmap[table]
        r = db.execute(f"select source_id from {t} where {idc}=?", (key,)).fetchone()
        if not r:
            raise KeyError(ref)
        return r["source_id"]

    def cite(self, ref):
        """(visible?, text). Not-yet-released evidence is reported as hidden, never shown."""
        sid = self.ref_source(ref)
        return self.source_visible(sid), (self.describe(ref) if self.source_visible(sid) else None)
