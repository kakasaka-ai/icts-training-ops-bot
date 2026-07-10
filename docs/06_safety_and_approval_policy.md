# Safety and approval policy

## Default state

Default state is dry-run.

No production write is allowed by default.

## Prohibited in early phases

- Production Salesforce update
- Production Slack post
- LINE sending
- ICTS AI account deletion
- Slack workspace or member deletion
- Google Drive permission changes
- Money Forward operation
- Browser-use write operation

## Approval required operations

Approval is required before:

- Salesforce attendance update
- Salesforce absence update
- Slack class-wide posting
- Slack member removal
- ICTS AI account removal
- LINE message sending
- Google Drive permission changes
- retirement / withdrawal status updates

## Required output before approval

Before approval, the system must show:

- target date
- target class
- target participant
- current value
- proposed value
- source evidence
- confidence / reason
- whether review is required

## Logging requirements

Every execution should log:

- run ID
- operator
- timestamp
- target date
- dry-run or production
- input source files / source IDs
- result counts
- errors
- approved by
- execution result
