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

RELEASES = {"day1": "2026-11-16", "day2": "2026-11-17"}  # Day 3/4 added when released

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
              "documents", "transcripts"):
        print(f"{t:<10} {d.execute(f'select count(*) from {t}').fetchone()[0]}")
