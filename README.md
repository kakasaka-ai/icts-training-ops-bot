# ICTS Training Ops Bot

This repository is for building training-operations automation with Codex.

## Source of truth

Salesforce is the source of truth.

RaySheet is treated as a Salesforce add-on / view.

The punch database in Google Sheets is an input source for attendance, not the master database.

## Priority roadmap

1. Attendance registration automation.
2. Punch-missing detection.
3. Class-wide Slack reminder automation.
4. Slack registration check.
5. Archive video guidance / recording announcement automation.
6. Withdrawal / retirement offboarding.

## First development goal

Do not connect to production APIs first.

The first goal is a CSV-based dry-run that reads fixture CSV files and outputs:

- attendance registration candidates
- punch-missing candidates
- unauthorized-absence candidates
- venue mismatch candidates
- name mismatch candidates
- duplicate punch candidates
- Markdown report
- CSV candidate file

## Initial local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install pytest pydantic python-dotenv
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
pip install pytest pydantic python-dotenv
```

## Future command target

Codex should build the code so this command works:

```bash
python -m training_ops.jobs.attendance_dry_run --date 2026-07-09
```

Expected outputs:

```text
reports/attendance_dry_run_2026-07-09.md
reports/attendance_candidates_2026-07-09.csv
```

## Important safety rule

Production writes are prohibited until dry-run, preview, approval, and logging are implemented.

Do not commit real credentials or real student data.
