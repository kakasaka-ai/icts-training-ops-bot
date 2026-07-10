# Attendance automation specification

## Goal

Automate attendance registration and punch-missing detection.

## Data sources

### Input source

- Punch database in Google Sheets
- Slack absence posts
- Salesforce training classes and participants

### Master record

- Salesforce

### View / editing UI

- RaySheet

## First implementation

Use CSV fixtures only.

Do not connect to production Google Sheets, Salesforce, or Slack.

## Matching priority

Use this priority when matching punch records to Salesforce participants:

1. Salesforce student ID
2. employee ID
3. email address
4. Slack user ID
5. LINE URL
6. name + company + venue
7. name only

Name-only matches must be review-required.

## Classification rules

| Classification | Rule | Auto-write allowed in first production version? |
|---|---|---|
| attendance_candidate | participant exists, punch exists, stable ID match, venue matches | yes, after approval |
| absent_with_notice | no punch, Slack absence notice exists | after approval |
| unauthorized_absence_candidate | no punch, no Slack absence notice | no |
| venue_mismatch | punch venue differs from scheduled venue | no |
| name_mismatch | no stable ID match; name-based candidate exists | no |
| duplicate_punch | multiple punch records for same participant/date | no |
| excluded | withdrawn, retired, optional graduate participation | no |

## Report sections

The Markdown report should include:

1. Summary counts.
2. Attendance registration candidates.
3. Absences with Slack notice.
4. Unauthorized absence candidates.
5. Review-required records.
6. Excluded records.
7. Errors and warnings.

## Candidate CSV columns

- target_date
- class_id
- participant_id
- salesforce_student_id
- employee_id
- student_name
- classification
- punch_id
- punched_at
- punch_venue
- scheduled_venue
- slack_absence_post_id
- confidence
- review_required
- reason
