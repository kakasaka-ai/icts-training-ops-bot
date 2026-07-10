# Salesforce source of truth

## Policy

Salesforce is the source of truth for training operations.

RaySheet is a Salesforce add-on / view.

Google Sheets, Slack, LINE, ICTS AI, and Google Drive are connected systems, not master databases.

## Required Salesforce information to confirm

Before production Salesforce integration, confirm these items with the Salesforce administrator:

1. Training class object API name.
2. Participant / roster object API name.
3. Attendance object API name.
4. Attendance status field API name.
5. Unauthorized absence checkbox field API name.
6. Training date field API name.
7. Training venue field API name.
8. Slack workspace ID field API name.
9. Slack channel ID field API name.
10. Slack user ID field API name.
11. ICTS AI registration status field API name.
12. LINE URL field API name.
13. Withdrawal / retirement status field API name.
14. Training end date field API name.
15. Whether Sandbox is available.
16. Whether API user has read/update permissions.
17. Whether external ID fields can be added.

## Recommended external ID for attendance

Use a stable key to avoid duplicate attendance records:

```text
attendance_key = salesforce_class_id + target_date + salesforce_student_id
```

Example:

```text
SFCLASS001-2026-07-09-SFSTUDENT001
```

## Write policy

Production write is allowed only after:

1. CSV dry-run works.
2. Google Sheets read-only works.
3. Salesforce Sandbox read-only works.
4. Salesforce Sandbox write works.
5. Slack approval flow works.
6. Production approval is explicitly given.
