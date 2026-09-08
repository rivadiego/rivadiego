# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
The only product here is `portfolio-tracker/` — a standalone Python script
(`build_workbook.py`) that generates an Excel workbook (`Portfolio_Tracker.xlsx`)
using `openpyxl`. There are **no services, servers, databases, tests, or lint
configs**. "Running the app" means regenerating the workbook.

### Build / run
From `portfolio-tracker/`:

```bash
python3 build_workbook.py
```

This overwrites `portfolio-tracker/Portfolio_Tracker.xlsx` and prints the output
path. Dependencies (`openpyxl`) are installed by the startup update script, so no
install step is needed at run time. See `portfolio-tracker/README.md` for the
workbook design and maintenance notes (README is in Italian).

### Non-obvious gotchas
- The generated workbook relies on **Microsoft 365 dynamic-array formulas**
  (`LET`, `FILTER`, `BYROW`, `LAMBDA`, `SWITCH`, `INDIRECT`). Formula results only
  evaluate in Microsoft 365 Excel — LibreOffice / older Excel (and openpyxl, which
  never calculates) will show the formulas but not computed KPIs. Do not expect to
  "see" calculated NAV/P&L values from within this VM.
- Running the script produces a byte-different `Portfolio_Tracker.xlsx` on every run
  (embedded metadata). Avoid committing that binary churn unless the workbook logic
  actually changed — `git checkout -- portfolio-tracker/Portfolio_Tracker.xlsx` to
  discard a pure-regeneration diff.
- `portfolio-tracker/source/` holds the original bank statements (`.xls`, `.pdf`)
  used as reference for the seeded sample data. They are **not read at runtime**;
  all sample rows are hardcoded in `build_workbook.py` (`sample_rows`).
- To verify a build without Excel, load it back with openpyxl and inspect
  `wb.sheetnames` / tables (expect sheets: `Leggimi, Summary, Config, Barclays ISA,
  Intesa Sanpaolo`).
