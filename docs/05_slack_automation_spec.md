# Slack automation specification

## Policy

Slack is the operations surface for notifications, previews, and approvals.

Use Slack API. Do not use browser-use for Slack operations unless explicitly approved.

## Priority Slack functions

1. Attendance dry-run report preview.
2. Punch-missing / unauthorized absence summary.
3. Class-wide reminder previews.
4. Slack registration check report.
5. Archive video post preview.
6. Withdrawal / retirement offboarding checklist.

## Reminder rules

### Progress survey reminder

- Target: currently active classes.
- Timing: monthly, before survey deadline.
- First implementation: preview only.

### Punch reminder

- Target: classes scheduled for the day.
- Timing:
  - 19:30 class -> 19:15 reminder
  - 20:00 class -> 19:45 reminder
- First implementation: preview only.

### Archive video reminder

- Target: class after training day.
- Must have verified recording URL.
- First implementation: preview only.

## Registration check

Compare Salesforce participants with Slack members.

Stable matching:

1. Slack user ID
2. email
3. employee ID
4. name only as review-required

## Approval flow target

Later production flow:

1. Bot posts preview to operations channel.
2. Human reviews.
3. Human presses approval button.
4. Bot updates Salesforce or posts to class channel.
5. Bot writes execution log.
