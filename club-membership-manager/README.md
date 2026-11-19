# Club Membership Manager

A menu-driven terminal app for running a college club: keep a member list, schedule events,
sign people up, and see how the club is doing. Built for FutureReady Hack (Project #29).
Pure Python standard library, nothing to install.

## Run it

```bash
python seed.py     # optional: loads 40 sample members and 6 events
python main.py
```

Needs Python 3.10 or newer. To run the tests: `python -m unittest discover -s tests`

## What it does

- Add, update, remove, list and search members (keyword, department, status filters)
- Create events and register or cancel members, with seat limits enforced
- Summary report: totals, dues rate, department/year charts, joining trend, top events and members
- Warnings: overdue dues, nearly full events, low turnout risk, empty past events, idle members
- Export a Markdown summary, a text audit log and a CSV member list to `exports/`
- Bulk import from CSV; rejected rows are written to `data/import_errors.log` with row numbers
- Data is saved to `data/club_data.json` after every change, so it survives restarts

## Rules the app enforces

| Field | Rule |
|---|---|
| Name | 2-60 chars, letters and `. ' -` only |
| Email | valid format, unique across members |
| Phone | 10-digit mobile starting 6-9 (`+91` and spaces are accepted) |
| Department | CSE, ECE, EEE, MECH, CIVIL, IT, MBA, OTHER |
| Year | 1 to 4 |
| Join date | `YYYY-MM-DD`, not in the future |
| Event capacity | 1 to 500 |
| Registration | active members only, no duplicates, no overbooking |

Type `cancel` at any prompt to back out.

## If the data file breaks

If `club_data.json` is missing it is created fresh. If it is corrupt, the app copies it to
`club_data.json.corrupt_<timestamp>` and starts clean instead of crashing. Records that don't
match the schema are skipped and counted.

## CSV import format

Required columns: `name,email,phone,department,year,join_date`. Optional: `status,dues_paid`.
Try `data/sample_import.csv`, which has a few deliberately bad rows.

## Layout

```
main.py            entry point
seed.py            sample data generator
club/models.py     Member and Event dataclasses
club/validation.py input checks and the retry-until-valid prompt helper
club/storage.py    JSON load/save with corruption recovery
club/logic.py      club rules, search, import, summary numbers, warnings
club/reports.py    text / Markdown / CSV output
club/cli.py        menus, tables, pagination
tests/             unit tests
```

## Demo script

1. Launch, show the menu, press `1` and type bad input (blank name, bad email, year 9) to show the validation.
2. Press `10` for the summary and `11` for warnings.
3. Press `13` to import `data/sample_import.csv` and show the error log.
4. Press `12` to export, then `0` to exit. Relaunch and show the data is still there.
