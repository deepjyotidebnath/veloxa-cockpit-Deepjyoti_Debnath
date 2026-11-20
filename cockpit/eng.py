"""Engineering facts derived from Jira, git, PagerDuty and the on-call rota. Every function takes a View so
point-in-time rules (known_by / as_of) apply. Nothing here predicts anything about a person: it measures work."""
import datetime as dt
from .view import View, EXPORT_DATE

PRIYA = "VX007"


def jira_open(v):
    """Open story points per assignee as of v.as_of (an issue is open if not resolved by then).
    The export only keeps final status, so historic 'In Progress' vs 'To Do' is unknowable; we only use resolved dates."""
    if not v.source_visible("SRC-JIRA"):
        return None
    d = v.as_of or EXPORT_DATE
    rows = v.db.execute("select emp_id, story_points p, resolved, created from jira_issues where created<=?", (d,)).fetchall()
    out, tot_open, tot = {}, 0, 0
    for r in rows:
        o = out.setdefault(r["emp_id"], dict(issues=0, points=0, open_issues=0, open_points=0))
        o["issues"] += 1; o["points"] += r["p"]; tot += r["p"]
        if not (r["resolved"] and r["resolved"] <= d):
            o["open_issues"] += 1; o["open_points"] += r["p"]; tot_open += r["p"]
    return dict(by_emp=out, open_points=tot_open, points=tot)


def last_resolved(v):
    r = v.db.execute("select max(resolved) m from jira_issues").fetchone()
    return r["m"]


def commit_profile(v, emp):
    if not v.source_visible("SRC-GIT"):
        return None
    d = v.as_of or "9999-12-31"
    r = v.db.execute("select count(*) n, sum(ist_hour>=22 or ist_hour<2) late, "
                     "count(distinct author_email) ids from commits where emp_id=? and effective_date<=?",
                     (emp, d)).fetchone()
    t = v.db.execute("select count(*) n from commits where effective_date<=?", (d,)).fetchone()["n"]
    return dict(n=r["n"], late=r["late"] or 0, ids=r["ids"], share=(r["n"] / t) if t else 0, total=t)


def oncall_load(v):
    if not v.source_visible("SRC-ROTA"):
        return None
    rows = v.db.execute("select * from oncall order by week_of").fetchall()
    if v.as_of:
        rows = [r for r in rows if r["week_of"] <= v.as_of]
    def cnt(emp, col):
        return sum(1 for r in rows if r[col] == emp)
    return dict(weeks=len(rows),
                sneha_primary=cnt("VX012", "primary_emp_id"), sneha_secondary=cnt("VX012", "secondary_emp_id"),
                contractor_primary=sum(1 for r in rows if r["primary_kind"] == "contractor"),
                contractor_secondary=sum(1 for r in rows if r["secondary_kind"] == "contractor"))


def incidents(v):
    if not v.source_visible("SRC-PD"):
        return None
    d = v.as_of or "9999-12-31"
    rows = v.db.execute("select * from incidents where effective_date<=? order by opened_utc", (d,)).fetchall()
    sev1 = [r for r in rows if r["severity"] == "SEV1"]
    aug1 = [r for r in sev1 if r["effective_date"].startswith("2026-08")]
    return dict(rows=rows, n=len(rows), sev1=sev1, aug_sev1=aug1,
                routing=sum(1 for r in rows if r["service"] == "routing-api"),
                hours=round(sum(r["duration_min"] for r in rows) / 60, 1))


def ga(v):
    if not v.source_visible("SRC-JIRA"):
        return None
    return v.db.execute("select * from jira_versions where version='Atlas GA'").fetchone()


def notice_end(start_iso, months=2):
    """Calendar-month arithmetic for a notice period starting on start_iso."""
    d = dt.date.fromisoformat(start_iso)
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    import calendar
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))
