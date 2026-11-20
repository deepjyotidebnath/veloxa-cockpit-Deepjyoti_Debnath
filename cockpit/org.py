"""Reporting lines, effective-dated (CEO voice note T6b: 'make sure the thing doesn't break when we move people around').

Rules this module enforces:
  * nothing is hard-coded about who reports to whom; everything is read from org_history;
  * 'recorded' rows come from the HR master and are facts; 'planned' rows are intentions and are NEVER returned
    unless the caller passes include_planned=True;
  * a person with a planned manager that does not exist yet (the CRO) keeps their recorded manager until a dated
    record says otherwise.
"""
from .view import View, EXPORT_DATE


def manager_of(v, emp_id, on=None, include_planned=False):
    on = on or v.as_of or EXPORT_DATE
    q = ("select * from org_history where emp_id=? and (from_date is null or from_date<=?) "
         "and (to_date is null or to_date>=?)")
    rows = v.db.execute(q, (emp_id, on, on)).fetchall()
    rows = [r for r in rows if (include_planned or r["status"] == "recorded")
            and (r["source_id"] == "SRC-EMP" or v.source_visible(r["source_id"]))]
    rows.sort(key=lambda r: r["status"] != "planned")   # a planned row, when asked for, outranks the recorded one
    return rows[0]["manager_id"] if rows else None


def reports_of(v, manager_id, on=None):
    on = on or v.as_of or EXPORT_DATE
    emps = [r["emp_id"] for r in v.db.execute("select distinct emp_id from org_history where status='recorded'")]
    return sorted(e for e in emps if manager_of(v, e, on) == manager_id)


def chain(v, emp_id, on=None):
    """Management chain up to the CEO. Stops at a missing/unknown manager and never loops."""
    out, seen, cur = [], {emp_id}, manager_of(v, emp_id, on)
    while cur and cur not in seen:
        out.append(cur)
        seen.add(cur)
        cur = manager_of(v, cur, on)
    return out


def planned_changes(v):
    return [dict(r) for r in v.db.execute("select * from org_history where status='planned'")
            if v.source_visible(r["source_id"])]
