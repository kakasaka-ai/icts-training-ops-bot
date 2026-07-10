# Open questions to confirm before production integration

## Salesforce

- What are the object API names for training class, participant, and attendance records?
- What field stores attendance status?
- What field stores unauthorized absence?
- Can an external ID field be added for attendance key?
- Is Salesforce Sandbox available?
- Does the API user have read/update permission?
- Is RaySheet displaying the same Salesforce object that the API will update?

## Google Sheets punch database

- Which spreadsheet ID is the production punch database?
- Which sheet/tab contains punch times?
- Is there a stable row ID or punch ID?
- Are employee ID or email included?
- How are venues represented?

## Slack

- Can each training workspace install the Slack app?
- Which channel is the operations channel?
- Which channel is the class-wide announcement channel?
- Which channel is the attendance confirmation channel?
- Is email visible through Slack API for matching?

## Google Drive / recordings

- Where are Meet recordings stored?
- Is there a consistent folder per teacher/class?
- Who owns the recordings?
- Can the API read file metadata and URLs?

## ICTS AI / LINE / Money Forward

- Is there an API or export available?
- If not, which screens need read-only browser-use checks?
