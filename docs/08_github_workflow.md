# GitHub workflow

## Repository

Recommended repository name:

```text
icts-training-ops-bot
```

Keep the repository private.

## Branch flow for one-person work

Even for one-person work, avoid direct changes to `main` after initial setup.

Recommended branches:

- `main`: stable files only
- `feature/attendance-dry-run`: attendance automation phase 1
- `feature/slack-preview`: Slack preview features
- `feature/salesforce-readonly`: Salesforce read-only integration

## Codex workflow

1. Create or select a feature branch.
2. Ask Codex to read `AGENTS.md`.
3. Ask Codex to implement one small phase.
4. Review the diff.
5. Run tests.
6. Merge only after the dry-run output and tests are acceptable.

## Do not commit

- `.env`
- real Salesforce exports
- real punch database data
- real Slack exports
- real LINE data
- real student or teacher personal information
- credentials or service account JSON files
