"""Load every released source into one SQLite database.

Two clocks on every record:
  effective_date : when the thing happened in Veloxa's world (None if unknown)
  released_on    : the day the hackathon pack made it available to us

`known_by` filters on released_on  ("what did we know on date X?")
`as_of`    filters on effective_date ("what was true in the company on date X?")
Keeping them separate is the whole point: the data room was exported on
31 Oct 2026 but we only *learned* about it on 16 Nov 2026.
"""
import csv
import email
import email.policy
import pathlib
import re
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = ROOT / "build" / "veloxa.db"

RELEASES = {"day1": "2026-11-16", "day2": "2026-11-17", "day3": "2026-11-18", "day4": "2026-11-19"}

SCHEMA = """
CREATE TABLE sources(source_id TEXT PRIMARY KEY, kind TEXT, title TEXT, path TEXT,
  released_on TEXT, effective_date TEXT, reliability TEXT, notes TEXT);
CREATE TABLE employees(emp_id TEXT PRIMARY KEY, full_name TEXT, work_email TEXT, department TEXT,
  title TEXT, manager_id TEXT, join_date TEXT, location TEXT, status TEXT, exit_date TEXT,
  source_id TEXT);
CREATE TABLE gl(row INT PRIMARY KEY, voucher TEXT, effective_date TEXT, vendor TEXT, ref TEXT,
  cost_centre TEXT, amount_inr INT, narration TEXT, entered_by TEXT, source_id TEXT);
CREATE TABLE payroll(emp_id TEXT, month TEXT, effective_date TEXT, days_in_month INT,
  days_payable INT, gross_inr INT, deductions_inr INT, net_inr INT, processed_by TEXT,
  source_id TEXT, PRIMARY KEY(emp_id, month));
CREATE TABLE reqs(req_id TEXT PRIMARY KEY, role TEXT, team TEXT, hiring_manager TEXT,
  opened TEXT, status TEXT, status_date TEXT, in_pipeline INT, notes TEXT, source_id TEXT);
CREATE TABLE pulse(quarter TEXT, team TEXT, effective_date TEXT, team_size INT, responses INT,
  engagement REAL, comments TEXT, source_id TEXT, PRIMARY KEY(quarter, team));
CREATE TABLE leave(leave_id TEXT PRIMARY KEY, emp_id TEXT, leave_type TEXT, from_date TEXT,
  to_date TEXT, days REAL, approved_by TEXT, source_id TEXT);
CREATE TABLE emails(email_id TEXT PRIMARY KEY, effective_date TEXT, sender TEXT, recipient TEXT,
  subject TEXT, body TEXT, source_id TEXT);
CREATE TABLE documents(doc_id TEXT PRIMARY KEY, kind TEXT, effective_date TEXT, title TEXT,
  body TEXT, source_id TEXT);
CREATE TABLE transcripts(t_id TEXT PRIMARY KEY, effective_date TEXT, speakers TEXT, body TEXT,
  source_id TEXT);
CREATE TABLE jira_issues(key TEXT PRIMARY KEY, type TEXT, summary TEXT, epic TEXT, epic_name TEXT,
  assignee_initials TEXT, emp_id TEXT, story_points INT, status TEXT, created TEXT, resolved TEXT,
  fix_version TEXT, source_id TEXT);
CREATE TABLE jira_versions(version TEXT PRIMARY KEY, release_date TEXT, original_release_date TEXT,
  last_changed TEXT, changed_by TEXT, source_id TEXT);
CREATE TABLE incidents(id TEXT PRIMARY KEY, severity TEXT, opened_utc TEXT, resolved_utc TEXT,
  effective_date TEXT, service TEXT, responder_as_written TEXT, responder_emp_id TEXT,
  responder_kind TEXT, duration_min INT, source_id TEXT);
CREATE TABLE oncall(week_of TEXT PRIMARY KEY, primary_as_written TEXT, secondary_as_written TEXT,
  primary_emp_id TEXT, secondary_emp_id TEXT, primary_kind TEXT, secondary_kind TEXT, source_id TEXT);
CREATE TABLE commits(sha TEXT PRIMARY KEY, author_email TEXT, emp_id TEXT, committed_at TEXT,
  effective_date TEXT, ist_hour INT, repo TEXT, message TEXT, files_changed INT, source_id TEXT);
CREATE TABLE invoices(inv_no TEXT PRIMARY KEY, vendor TEXT, invoice_date TEXT, period TEXT,
  net_inr INT, gst_inr INT, total_inr INT, source_id TEXT);
-- Reporting lines over time. 'recorded' rows come from the HR master; 'planned' rows are stated intentions
-- (e.g. CEO voice note T6b) that are NOT facts until a dated record confirms them.
CREATE TABLE org_history(emp_id TEXT, manager_id TEXT, from_date TEXT, to_date TEXT, status TEXT, source_id TEXT);
"""

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
QUARTER_END = {"Oct-Dec": "12-31", "Jan-Mar": "03-31", "Apr-Jun": "06-30", "Jul-Sep": "09-30"}


def _rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _month_end(label):  # "Feb-2026" -> 2026-02-28 (payroll runs on month; use month end)
    mon, year = label.split("-")
    m, y = MONTHS[mon], int(year)
    last = {1: 31, 2: 29 if y % 4 == 0 else 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31,
            8: 31, 9: 30, 10: 31, 11: 30, 12: 31}[m]
    return f"{y}-{m:02d}-{last:02d}"


def _quarter_effective(q):
    span, year = q.rsplit(" ", 1)
    end = QUARTER_END[span]
    y = int(year)
    d = f"{y}-{end}"
    # Evidence override: Deepa's 29 Sep 2026 email already quotes the Jul-Sep result,
    # so results were available before the quarter closed.
    return "2026-09-29" if q == "Jul-Sep 2026" else d


def _email_date(h):
    from email.utils import parsedate_to_datetime
    return parsedate_to_datetime(h).date().isoformat()


# Entity resolution for the engineering exports (reasoning in TRANSCRIPT_NOTES.md N-25..N-28)
JIRA_INITIALS = {"PN": "VX007", "RV": "VX018", "AD": "VX009", "SK": "VX012"}
GIT_EMAILS = {"priya.n@veloxa.in": "VX007", "pnair@users.noreply.github.com": "VX007",
              "arjun@veloxa.in": "VX009", "rahul.v@veloxa.in": "VX018", "sneha.k@veloxa.in": "VX012",
              "vikram@veloxa.in": "VX004"}
# "Sneha" = employee Sneha Kulkarni; "Snehal" = contractor S. Patil (Patil Infra Services); NOT the same person.
RESPONDERS = {"Sneha": ("VX012", "employee"), "Snehal": (None, "contractor"),
              "Arjun": ("VX009", "employee"), "Priya": ("VX007", "employee")}
IST_OFFSET = 5.5 * 3600


def _ist(ts):
    import datetime as dt
    d = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    return d


def build(db_path=DB_PATH):
    db_path = pathlib.Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    src = []

    def S(sid, kind, title, path, day, eff, rel, notes=""):
        src.append((sid, kind, title, str(path), RELEASES[day], eff, rel, notes))
        return sid

    # ---------------- Day 1 ----------------
    d1 = DATA / "day1"
    s = S("SRC-EMP", "export", "Keka employee master (employees only)", "day1/employees.csv",
          "day1", "2026-10-31", "high",
          "Employees only, no contractors. No exited rows -> cannot compute historic attrition.")
    for r in _rows(d1 / "employees.csv"):
        db.execute("INSERT INTO employees VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                   (r["emp_id"], r["full_name"], r["work_email"], r["department"], r["title"],
                    r["manager_id"] or None, r["join_date"], r["location"], r["status"],
                    r["exit_date"] or None, s))
    s = S("SRC-GL", "export", "Zoho Books GL Apr-Sep 2026 (selected cost centres)",
          "day1/gl.csv", "day1", "2026-09-30", "high",
          "Selected cost centres only; no revenue lines.")
    for r in _rows(d1 / "gl.csv"):
        db.execute("INSERT INTO gl VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (int(r["row"]), r["voucher"], r["txn_date"], r["vendor"], r["ref"],
                    r["cost_centre"], int(r["amount_inr"]), r["narration"], r["entered_by"], s))
    s = S("SRC-PAY", "export", "Payroll register Jan-Mar 2026 (pre-Keka workbook)",
          "day1/payroll_jan_mar_2026.csv", "day1", "2026-03-31", "high",
          "Individual salaries: restricted, see DECISIONS.md D-07.")
    for r in _rows(d1 / "payroll_jan_mar_2026.csv"):
        db.execute("INSERT INTO payroll VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (r["emp_id"], r["month"], _month_end(r["month"]), int(r["days_in_month"]),
                    int(r["days_payable"]), int(r["gross_inr"]), int(r["deductions_inr"]),
                    int(r["net_inr"]), r["processed_by"], s))

    docs = [("board_q2", "board_update", "2026-07-08", "Board update Apr-Jun 2026",
             "board_update_apr_jun_2026.md", "SRC-BOARD-Q2"),
            ("board_q3", "board_update", "2026-10-06", "Board update Jul-Sep 2026",
             "board_update_jul_sep_2026.md", "SRC-BOARD-Q3")]
    for did, kind, eff, title, fn, sid in docs:
        S(sid, "document", title, f"day1/documents/{fn}", "day1", eff, "medium",
          "Management-reported, unaudited.")
        db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?)",
                   (did, kind, eff, title, (d1 / "documents" / fn).read_text(), sid))

    def transcript(tid, day, fn, speakers, rel_note):
        sid = f"SRC-{tid}"
        S(sid, "transcript", tid, f"{day}/transcripts/{fn}", day, None, "low", rel_note)
        db.execute("INSERT INTO transcripts VALUES(?,?,?,?,?)",
                   (tid, None, speakers, (DATA / day / "transcripts" / fn).read_text(), sid))

    transcript("T1", "day1", "T1_ceo_kickoff.md", "Ananya R.; Speaker 2", "Machine-generated; call date unknown")
    transcript("T2", "day1", "T2_cfo_call.md", "Meera I.; Ananya R.", "Poor audio; call date unknown")

    def emails(day, folder_note):
        for p in sorted((DATA / day / "emails").glob("*.eml")):
            m = email.message_from_bytes(p.read_bytes(), policy=email.policy.default)
            sid = f"SRC-EML-{p.stem}"
            eff = _email_date(m["Date"])
            S(sid, "email", f"{p.stem}.eml", f"{day}/emails/{p.name}", day, eff, "high", folder_note)
            db.execute("INSERT INTO emails VALUES(?,?,?,?,?,?,?)",
                       (p.stem, eff, m["From"], m["To"], m["Subject"], m.get_content().strip(), sid))

    emails("day1", "Selected threads only; numbering has gaps")

    # ---------------- Day 2 ----------------
    d2 = DATA / "day2"
    transcript("T3", "day2", "T3_head_of_people.md", "Deepa J.; Ananya R.; Rohan",
               "Good audio; call date unknown but after 15 Sep 2026")
    transcript("T6a", "day2", "T6a_ceo_voice_note.md", "Ananya R.", "Voice note; date unknown")
    emails("day2", "Selected threads only; numbering has gaps")
    S("SRC-LETTER-SM", "document", "Resignation letter, Siddharth Mehta", "day2/documents/resignation_letter_sm.md",
      "day2", "2026-09-15", "high")
    db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?)",
               ("letter_sm", "letter", "2026-09-15", "Resignation letter, Siddharth Mehta",
                (d2 / "documents" / "resignation_letter_sm.md").read_text(), "SRC-LETTER-SM"))
    s = S("SRC-HIRE", "export", "Keka Hire requisitions", "day2/hiring_tracker.csv", "day2",
          "2026-10-31", "high", "Snapshot at export: only current status, no history. REQ-012 absent.")
    for r in _rows(d2 / "hiring_tracker.csv"):
        db.execute("INSERT INTO reqs VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (r["req_id"], r["role"], r["team"], r["hiring_manager"], r["opened"], r["status"],
                    r["status_date"], int(r["in_pipeline"]), r["notes"], s))
    s = S("SRC-PULSE", "export", "Culture Amp pulse by team", "day2/pulse_survey.csv", "day2",
          "2026-10-31", "high", "Team level only; comments suppressed (team < 6).")
    for r in _rows(d2 / "pulse_survey.csv"):
        db.execute("INSERT INTO pulse VALUES(?,?,?,?,?,?,?,?)",
                   (r["quarter"], r["team"], _quarter_effective(r["quarter"]), int(r["team_size"]),
                    int(r["responses"]), float(r["engagement_1_5"]), r["comments"], s))
    s = S("SRC-LEAVE", "export", "Leave register (Google Sheet, Nov 2025-Oct 2026)",
          "day2/leave_register.csv", "day2", "2026-10-31", "medium",
          "Hand-maintained sheet; names abbreviated; emp_id resolved by us.")
    for r in _rows(d2 / "leave_register.csv"):
        db.execute("INSERT INTO leave VALUES(?,?,?,?,?,?,?,?)",
                   (r["leave_id"], r["emp_id"], r["leave_type"], r["from_date"], r["to_date"],
                    float(r["days"]), r["approved_by"], s))

    # ---------------- Day 3 ----------------
    d3 = DATA / "day3"
    transcript("T4", "day3", "T4_head_of_marketing.md", "Nikhil B.; Speaker 2", "Fair audio; call date unknown, after 17 Sep 2026")
    transcript("T5", "day3", "T5_vp_engineering.md", "Vikram M.; Ananya R.", "4-minute audio gap; call date unknown")
    transcript("T6b", "day3", "T6b_ceo_voice_note.md", "Ananya R.", "Voice note; date unknown")
    emails("day3", "Selected threads only; numbering has gaps")
    for did, kind, eff, title, fn, sid, rel in [
            ("launch_kit", "launch_kit", "2026-07-21", "Atlas launch kit v1", "atlas_launch_kit_v1.md",
             "SRC-LAUNCH", "medium"),
            ("invoice_pis114", "invoice", "2026-10-01", "Invoice PIS-114 (Patil Infra Services)",
             "invoice_pis_114.md", "SRC-INV-PIS114", "high")]:
        S(sid, "document", title, f"day3/documents/{fn}", "day3", eff, rel)
        db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?)",
                   (did, kind, eff, title, (d3 / "documents" / fn).read_text(), sid))
    db.execute("INSERT INTO invoices VALUES(?,?,?,?,?,?,?,?)",
               ("PIS-114", "Patil Infra Services", "2026-10-01", "2026-09", 120000, 21600, 141600, "SRC-INV-PIS114"))
    epics = {r["key"]: r["epic_name"] for r in _rows(d3 / "jira_epics.csv")}
    s = S("SRC-JIRA", "export", "Jira export, project ATLAS (assignee as initials)", "day3/jira_issues.csv",
          "day3", "2026-10-31", "high", "Issues, epics and versions sheets of one workbook. Initials mapped by us.")
    for r in _rows(d3 / "jira_issues.csv"):
        db.execute("INSERT INTO jira_issues VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (r["key"], r["type"], r["summary"], r["epic"], epics[r["epic"]], r["assignee_initials"],
                    JIRA_INITIALS[r["assignee_initials"]], int(r["story_points"]), r["status"], r["created"],
                    r["resolved"] or None, r["fix_version"], s))
    for r in _rows(d3 / "jira_versions.csv"):
        db.execute("INSERT INTO jira_versions VALUES(?,?,?,?,?,?)",
                   (r["version"], r["release_date"], r["original_release_date"], r["last_changed"], r["changed_by"], s))
    s = S("SRC-PD", "export", "PagerDuty incidents Aug-Oct 2026", "day3/incidents.csv", "day3", "2026-10-31",
          "high", "Timestamps are UTC (Z); emails are IST. Responder is a first name only.")
    for r in _rows(d3 / "incidents.csv"):
        emp, kind = RESPONDERS[r["responder_as_written"]]
        o, c = _ist(r["opened_utc"]), _ist(r["resolved_utc"])
        db.execute("INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                   (r["id"], r["severity"], r["opened_utc"], r["resolved_utc"], o.date().isoformat(), r["service"],
                    r["responder_as_written"], emp, kind, int((c - o).total_seconds() // 60), s))
    s = S("SRC-ROTA", "export", "On-call rota (team wiki table, copied)", "day3/oncall_rota.csv", "day3",
          "2026-10-31", "medium", "Hand-copied wiki table; disagrees with email 08 on when the contractor started.")
    for r in _rows(d3 / "oncall_rota.csv"):
        (pe, pk), (se, sk) = (RESPONDERS[r["primary_as_written"]], RESPONDERS[r["secondary_as_written"]])
        db.execute("INSERT INTO oncall VALUES(?,?,?,?,?,?,?,?)",
                   (r["week_of"], r["primary_as_written"], r["secondary_as_written"], pe, se, pk, sk, s))
    s = S("SRC-GIT", "export", "Git log (all four repos, Nov 2025-Oct 2026)", "day3/git_log.csv", "day3",
          "2026-10-30", "high", "Priya appears under two author emails; both mapped to VX007 (N-26). Times are UTC.")
    for r in _rows(d3 / "git_log.csv"):
        t = _ist(r["committed_at"])
        db.execute("INSERT INTO commits VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (r["sha"], r["author_email"], GIT_EMAILS[r["author_email"]], r["committed_at"],
                    t.date().isoformat(), t.hour, r["repo"], r["message"], int(r["files_changed"]), s))

    # ---------------- Day 4 ----------------
    transcript("T6c", "day4", "T6c_ceo_voice_note.md", "Ananya R.", "Voice note; date unknown")
    transcript("T6d", "day4", "T6d_ceo_voice_note.md", "Ananya R.", "Voice note; says 'this morning'; date unknown; "
               "reports an event with no system record (the data room ends 31 Oct)")

    # ---------------- Reporting lines ----------------
    for e in db.execute("select emp_id, manager_id, join_date, exit_date from employees where manager_id is not null"):
        db.execute("INSERT INTO org_history VALUES(?,?,?,?,?,?)",
                   (e[0], e[1], e[2], e[3], "recorded", "SRC-EMP"))
    # T6b: Marketing to report to a new CRO "from next month, or the month after". Nobody holds the role,
    # no date is firm: stored as PLANNED, with no manager id and no start date, and never used as fact.
    db.execute("INSERT INTO org_history VALUES(?,?,?,?,?,?)", ("VX006", "CRO-TBD", None, None, "planned", "SRC-T6b"))

    db.executemany("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?)", src)
    db.commit()
    return db


_CONN = {}


def connect(db_path=DB_PATH):
    """One shared read connection per database file (the DB is rebuilt by `build`, never mutated at query time)."""
    key = str(db_path)
    if key not in _CONN:
        if not pathlib.Path(db_path).exists():
            build(db_path).close()
        _CONN[key] = sqlite3.connect(db_path)
        _CONN[key].row_factory = sqlite3.Row
    return _CONN[key]


if __name__ == "__main__":
    d = build()
    for t in ("sources", "employees", "gl", "payroll", "reqs", "pulse", "leave", "emails",
              "documents", "transcripts", "jira_issues", "jira_versions", "incidents", "oncall", "commits",
              "invoices", "org_history"):
        print(f"{t:<10} {d.execute(f'select count(*) from {t}').fetchone()[0]}")
