# ICTS Training Ops Bot

ICTS の研修運用を段階的に自動化する Python プロジェクトです。

Salesforce を正本とし、RaySheet は Salesforce のビューとして扱います。打刻データベースと Slack 欠席連絡は照合用の入力であり、正本ではありません。

## Phase 1: 出席判定 CSV dry-run

Phase 1 は fixture CSV だけを読み、Salesforce/RaySheet に反映する候補をローカルファイルとして生成します。

- Salesforce、RaySheet、Slack、Google Sheets、LINE、ICTS AI には接続しません。
- 外部 API 通信、投稿、更新は行いません。
- 氏名のみ一致、会場不一致、重複打刻、無断欠席候補、対象外 status は必ず確認対象です。
- `reports/` は実行時の dry-run 出力であり、Git にはコミットしません。

## セットアップ

リポジトリのルートで実行します。Python 3.11 以上を使用してください。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install '.[dev]'
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install ".[dev]"
```

## 実行方法

```bash
python -m training_ops.jobs.attendance_dry_run --date 2026-07-10
```

正常終了すると次のように表示されます。

```text
Markdown report: reports/attendance_dry_run_2026-07-10.md
Candidate CSV: reports/attendance_candidates_2026-07-10.csv
Candidates: 3 (dry-run; external connections: 0; run_id: ...)
```

生成物:

- `reports/attendance_dry_run_YYYY-MM-DD.md`
- `reports/attendance_candidates_YYYY-MM-DD.csv`

入力や出力先は `--training-classes`、`--participants`、`--punch-records`、`--slack-absence-posts`、`--output-dir` で変更できます。

## 判定内容

| classification | 条件 | `review_required` |
|---|---|---|
| `attendance_candidate` | 安定 ID と会場が一致する打刻あり | `false` |
| `absent_with_notice` | 打刻なし、class ID と employee ID が一致する Slack 欠席連絡あり | `false` |
| `unauthorized_absence_candidate` | 打刻なし、安定 ID の Slack 欠席連絡なし | `true` |
| `venue_mismatch` | 安定 ID は一致するが会場不一致 | `true` |
| `name_mismatch` | 打刻または欠席連絡が氏名のみ一致 | `true` |
| `duplicate_punch` | 同一参加者・同一日の安定 ID 一致打刻が複数 | `true` |
| `excluded` | 離脱、退職、卒業任意参加 | `true` |

`review_required=false` も自動更新を意味しません。Phase 1 は候補を出力するだけです。

## 照合順序

Salesforce の参加者情報を基準に、現在の打刻 CSV では次の順序で照合します。

1. `employee_id`
2. `email`
3. 氏名（確認対象のみ）

将来、打刻側に Salesforce student ID が追加された場合は最優先で利用します。

## 入力 CSV

既定では次の偽データ fixture を読みます。

- `tests/fixtures/training_classes.csv`: Salesforce 研修スナップショット
- `tests/fixtures/participants.csv`: Salesforce 参加者スナップショット
- `tests/fixtures/punch_records.csv`: 打刻データベースの CSV スナップショット
- `tests/fixtures/slack_absence_posts.csv`: Slack 欠席連絡の CSV スナップショット

実在する学生・従業員の情報や、本番サービスから取得した CSV をコミットしないでください。

## 構造化ログ

実行開始・完了・失敗は JSON 形式で標準エラーに出力されます。ログには `run_id`、実行者、時刻、対象日、dry-run モード、入力ファイル、件数、警告、エラー、承認者、実行結果が含まれます。

実行者は `TRAINING_OPS_OPERATOR` 環境変数で指定でき、未指定時は `local` です。

## テスト

```bash
python -m pytest
```

テストは一時ディレクトリだけにレポートを生成し、ネットワーク接続が発生しないことも検証します。

## 今後の安全条件

本番更新を追加するには、dry-run、差分プレビュー、人による明示承認、実行ログがすべて必要です。Phase 1 には本番更新コードや外部 API クライアントを含めません。
