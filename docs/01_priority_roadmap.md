# Priority roadmap

## Priority 1: Attendance registration automation

Goal: Use punch database records to create Salesforce attendance registration candidates.

First phase:

- CSV-based dry-run only.
- Generate attendance candidate CSV.
- Generate Markdown report.
- Do not update Salesforce.

Later phases:

- Read punch database from Google Sheets API.
- Read participants from Salesforce Sandbox.
- Write approved records to Salesforce Sandbox.
- Write approved records to production Salesforce.

## Priority 2: Punch-missing detection

Goal: Detect participants who should have attended but have no punch record.

Classifications:

- absent with Slack notice
- unauthorized absence candidate
- venue mismatch candidate
- name mismatch candidate
- duplicate punch candidate

This should be developed together with Priority 1 because the data and logic overlap.

## Priority 3: Class-wide Slack reminder automation

Goal: Replace manual Slack `/remind` setup with preview-based automated reminders.

Targets:

- progress survey reminder
- attendance punch reminder
- archive video reminder
- new training tool-registration guidance

First phase: message previews only.

## Priority 4: Slack registration check

Goal: Compare Salesforce participant list with Slack workspace members.

Use:

- Slack user ID
- email address
- employee ID
- name only as review-required fallback

## Priority 5: Archive video guidance

Goal: Detect recording availability and prepare Slack announcement previews.

First phase:

- check recording file existence
- check file name
- check folder destination
- create Slack post preview

Do not automatically announce missing or unverified recordings.

## Priority 6: Withdrawal / retirement offboarding

Goal: Create checklists for withdrawal / retirement processing.

Initial output only:

- Salesforce target
- Slack removal target
- ICTS AI removal target
- progress sheet update target
- teacher notification draft
- student notification draft

Do not automatically remove users or send messages in the first version.
