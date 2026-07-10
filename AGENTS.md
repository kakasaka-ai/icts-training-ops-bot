# AGENTS.md

## Project purpose

This repository is for automating ICTS training operations with Codex.

The system supports:

- Attendance registration automation from the punch database into Salesforce/RaySheet.
- Punch-missing and unauthorized-absence detection.
- Slack reminder automation.
- Slack workspace registration checks.
- Archive video check and Slack announcement previews.
- Withdrawal / retirement offboarding checklists.

## User skill assumption

The main operator can teach HTML/CSS, but has only basic Java knowledge and is not deeply familiar with object-oriented programming, classes, or frameworks.

When proposing or writing code:

- Prefer small, readable Python modules over complex framework-heavy designs.
- Explain where to run commands and what output to expect.
- Do not assume the operator understands dependency injection, abstract classes, decorators, or complex design patterns.
- Add comments where business logic is important.
- Keep README instructions practical and step-by-step.
- Avoid over-engineering.

## Most important business rule

Salesforce is the source of truth.

Do not introduce PostgreSQL, SQLite, Airtable, Supabase, or another database as the master source unless explicitly requested by the user.

RaySheet is treated as a Salesforce add-on / view, not as a separate master database.

The punch database in Google Sheets is an input source for attendance, not the master database.

If temporary storage is needed, describe it only as one of the following:

- cache
- execution log
- retry queue
- dry-run output
- audit log

Never describe temporary storage as the master database.

## Current operations to respect

Current operations use:

- Salesforce / RaySheet for training lists, participant lists, attendance, training status, orientation status, withdrawal, retirement, Slack registration, and ICTS AI status.
- Google Sheets as the punch database and operational sheets.
- Slack for class-wide announcements, attendance reminders, progress survey reminders, recording reminders, and workspace registration checks.
- LINE for student/admin communication, Q&A, training guidance, graduation guidance, and individual messages.
- ICTS AI for learning support and training account management.
- Google Drive for recordings, progress sheets, seat charts, and operational files.
- Money Forward for contracts, invoices, and payment-related work.

## Priority order

Build features in this order:

1. Attendance registration automation.
2. Punch-missing detection.
3. Class-wide Slack reminder automation.
4. Slack registration check.
5. Archive video guidance / recording announcement automation.
6. Withdrawal / retirement offboarding.

Attendance registration and punch-missing detection should be built together because they use the same inputs.

## Safety rules

Default mode is dry-run.

Codex must not create code that updates production Salesforce, Slack, LINE, ICTS AI, Google Drive, Google Sheets, or Money Forward without all of the following:

1. dry-run output
2. human-readable diff / preview
3. explicit human approval or Slack approval
4. execution log

Never hard-code:

- Salesforce credentials
- Slack bot tokens
- LINE tokens
- Google credentials
- ICTS AI credentials
- Money Forward credentials
- personal information
- real employee names
- real student data

Use environment variables only. Use `.env.example` for examples. Do not create `.env` with real secrets.

## Salesforce rules

Salesforce is the master record.

Use Salesforce IDs or stable external IDs whenever possible.

For student matching, prefer this order:

1. Salesforce record ID
2. employee ID
3. email address
4. Slack user ID
5. LINE URL
6. name + company + venue
7. name only as a last resort

Name-only matching must not be auto-written to Salesforce. It must be treated as a review-required candidate.

All Salesforce write operations must be behind an approval layer.

The first implementation must support read-only mode and dry-run mode.

## Attendance automation rules

The punch database is the attendance input source.

Salesforce is the final master record for attendance.

RaySheet should reflect Salesforce updates.

Attendance automation must classify records into:

- present / attendance registration candidate
- absent with Slack notice
- unauthorized absence candidate
- venue mismatch candidate
- name mismatch candidate
- duplicate punch candidate
- excluded because of withdrawal, retirement, or optional graduate participation

Do not automatically write the following without human review:

- unauthorized absence
- venue mismatch
- name-only match
- duplicate punch
- withdrawn / retired / optional graduate cases

## Slack rules

Use Slack API for Slack operations.

Do not use browser-use to operate Slack unless Slack API is unavailable for the specific task.

Use Slack user IDs and channel IDs. Do not rely on channel names or display names for production logic.

All automated Slack posts must support:

- preview mode
- dry-run mode
- approval mode
- execution logs

Do not use `@channel` in test environments unless explicitly requested.

## Browser-use rules

Browser-use is allowed only for tools where stable APIs are unavailable or not yet approved.

Browser-use may be used for read-only checks such as:

- ICTS AI admin screen checks
- LINE admin screen checks
- RaySheet screen checks if Salesforce API access is not available
- Money Forward checks if API or CSV export is not available

Browser-use must start as read-only.

Do not allow browser-use to submit production forms, delete accounts, change statuses, or send messages unless explicitly approved.

Do not store passwords, 2FA codes, or session cookies in this repository.

## Development rules

Use Python unless another language is explicitly requested.

Recommended stack:

- Python 3.11+
- pytest for tests
- pydantic for schemas
- python-dotenv for local development
- Google Sheets API only after CSV dry-run works
- Slack Bolt for Python only after Slack preview works
- simple-salesforce or Salesforce REST API client only after Salesforce object/field names are confirmed

Every feature must include:

- unit tests
- dry-run behavior
- structured logs
- clear error messages
- README usage instructions

## First-phase scope

Phase 1 must not update production systems automatically.

Phase 1 should build:

1. CSV-based attendance dry-run.
2. Attendance registration candidate extraction.
3. Punch-missing and unauthorized-absence candidate extraction.
4. Markdown report output.
5. CSV candidate output.
6. Tests for matching and classification.

## Definition of done

A task is done only when:

- tests pass
- dry-run output is shown
- no secrets are committed
- no real personal data is included
- README is updated
- risky operations are behind approval
- Salesforce remains the source of truth
