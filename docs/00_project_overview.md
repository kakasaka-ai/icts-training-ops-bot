# Project overview

This project automates ICTS training operations with Salesforce as the source of truth.

## Main policy

- Salesforce is the master record.
- RaySheet is a Salesforce add-on / view.
- Google Sheets punch database is an input source.
- Slack is the operational notification and approval surface.
- LINE remains the student/admin communication channel.
- Browser-use is read-only at first and only for systems without approved APIs.

## Priority order

1. Attendance registration automation.
2. Punch-missing detection.
3. Class-wide Slack reminder automation.
4. Slack registration check.
5. Archive video guidance / recording announcement automation.
6. Withdrawal / retirement offboarding.

## First milestone

Build a CSV-based attendance dry-run. Do not connect to production Salesforce, Slack, LINE, ICTS AI, Google Drive, Google Sheets, or Money Forward in the first milestone.
