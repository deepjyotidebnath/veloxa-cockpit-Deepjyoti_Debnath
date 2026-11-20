"""The committed CSVs must match the original export files in data/raw (skipped if openpyxl is not installed)."""
import csv, pathlib, unittest
try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAIRS = [("day1/Employee_Master.xlsx", "day1/employees.csv", "Emp ID", 0),
         ("day1/GL_Export_Apr-Sep_2026.xlsx", "day1/gl.csv", "Txn Date", 1),
         ("day1/Payroll_Register_Jan-Mar_2026.xlsx", "day1/payroll_jan_mar_2026.csv", "Emp ID", 0),
         ("day2/Hiring_Tracker.xlsx", "day2/hiring_tracker.csv", "Req ID", 0),
         ("day2/Pulse_Survey.xlsx", "day2/pulse_survey.csv", "Quarter", 0),
         ("day3/Jira_Export_ATLAS.xlsx", "day3/jira_issues.csv", "Key", 0)]


def norm(c):
    c = str(c).strip()
    try:
        return str(float(c)).rstrip("0").rstrip(".")
    except ValueError:
        return c


@unittest.skipIf(openpyxl is None, "openpyxl not installed")
class Fidelity(unittest.TestCase):
    def test_csv_matches_original(self):
        for raw, mine, marker, drop_first_cols in PAIRS:
            ws = openpyxl.load_workbook(ROOT / "data/raw" / raw, data_only=True).worksheets[0]
            rows = [["" if c is None else c for c in r] for r in ws.iter_rows(values_only=True)]
            i = next(k for k, r in enumerate(rows) if r and r[0] == marker)
            orig = [[norm(c) for c in r] for r in rows[i + 1:] if any(str(c).strip() for c in r)]
            mine_rows = [[norm(c) for c in r][drop_first_cols:] for r in list(csv.reader(open(ROOT / "data" / mine)))[1:]]
            self.assertEqual(mine_rows, orig, mine)

    def test_leave_register_matches_original(self):
        ws = openpyxl.load_workbook(ROOT / "data/raw/day2/Leave_Register.xlsx", data_only=True).worksheets[0]
        rows = [["" if c is None else c for c in r] for r in ws.iter_rows(values_only=True)]
        i = next(k for k, r in enumerate(rows) if r and r[0] == "Employee")
        orig = [[norm(c) for c in r] for r in rows[i + 1:] if any(str(c).strip() for c in r)]
        mine = [[norm(c) for c in (r[1], r[3], r[4], r[5], r[6], r[7])]
                for r in list(csv.reader(open(ROOT / "data/day2/leave_register.csv")))[1:]]
        self.assertEqual(mine, orig)


if __name__ == "__main__":
    unittest.main()
