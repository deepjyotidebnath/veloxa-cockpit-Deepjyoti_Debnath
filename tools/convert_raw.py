"""Rebuild the Day 3 CSVs in data/day3/ from the original files in data/raw/ (needs openpyxl; dev-only).
Day 1/2 CSVs were verified against data/raw by tests/test_integrity.py (also needs openpyxl; skipped without it)."""
import csv, pathlib
import openpyxl

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "day3"


def sheet(path, name=None, header_row_marker=None):
    ws = openpyxl.load_workbook(path, data_only=True)[name] if name else openpyxl.load_workbook(path, data_only=True).active
    rows = [["" if c is None else c for c in r] for r in ws.iter_rows(values_only=True)]
    i = next(k for k, r in enumerate(rows) if r and r[0] == header_row_marker)
    return rows[i], [r for r in rows[i + 1:] if any(str(c).strip() for c in r)]


def write(name, header, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    h, r = sheet(RAW / "day3/Jira_Export_ATLAS.xlsx", "Issues", "Key")
    write("jira_issues.csv", ["key", "type", "summary", "epic", "assignee_initials", "story_points", "status",
                              "created", "resolved", "fix_version"], r)
    h, r = sheet(RAW / "day3/Jira_Export_ATLAS.xlsx", "Epics", "Key")
    write("jira_epics.csv", ["key", "epic_name"], r)
    h, r = sheet(RAW / "day3/Jira_Export_ATLAS.xlsx", "Versions", "Version")
    write("jira_versions.csv", ["version", "release_date", "original_release_date", "last_changed", "changed_by"], r)
    h, r = sheet(RAW / "day3/Incidents_Aug-Oct_2026.xlsx", "Incidents", "ID")
    write("incidents.csv", ["id", "severity", "opened_utc", "resolved_utc", "service", "responder_as_written"], r)
    h, r = sheet(RAW / "day3/OnCall_Rota.xlsx", "On-call", "Week of")
    write("oncall_rota.csv", ["week_of", "primary_as_written", "secondary_as_written"],
          [[str(c)[:10] if i == 0 else c for i, c in enumerate(row)] for row in r])
    print("ok")
