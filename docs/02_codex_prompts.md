# Codex prompts

Use these prompts in Codex in order.

## Common instruction prefix

```text
AGENTS.md を読んで、そのルールに従って作業してください。

このプロジェクトでは Salesforce を正本とします。
RaySheet は Salesforce のビューとして扱います。
本番 API には接続しないでください。
本番更新、Slack 本番投稿、LINE 送信、ICTS AI 操作、Google Drive 権限変更は行わないでください。
最初は dry-run、preview、test を重視してください。
```

## Phase 1: attendance dry-run

```text
AGENTS.md を読んで、そのルールに従ってください。

出席登録自動化と打刻漏れ検知の Phase 1 を作ってください。
本番 API には接続せず、CSV ベースの dry-run だけを実装してください。

目的:
打刻データベースの記録をもとに、Salesforce/RaySheet へ反映する出欠結果の候補を作る。

前提:
- Salesforce を正本とする
- 打刻データベースは入力元として扱う
- RaySheet は Salesforce のビューとして扱う
- 本番 Salesforce 更新はしない
- Slack 投稿もしない
- 氏名のみ一致は自動反映対象にしない

入力 CSV:
1. tests/fixtures/punch_records.csv
2. tests/fixtures/training_classes.csv
3. tests/fixtures/participants.csv
4. tests/fixtures/slack_absence_posts.csv

出力:
- reports/attendance_dry_run_YYYY-MM-DD.md
- reports/attendance_candidates_YYYY-MM-DD.csv

判定:
- punch あり + 参加予定あり + 会場一致 + ID一致 → 出席登録候補
- punch なし + Slack 欠席連絡あり → 連絡あり欠席
- punch なし + Slack 欠席連絡なし → 無断欠席候補
- 会場不一致 → 確認対象
- 氏名のみ一致 → 確認対象
- status が離脱/退職/卒業任意参加 → 自動反映対象外
- 重複打刻 → 確認対象

完了条件:
- pytest が通る
- python -m training_ops.jobs.attendance_dry_run --date YYYY-MM-DD でレポートが出る
- Salesforce、Slack、Google Sheets には接続しない
- README に実行方法を書く
```

## Phase 2: Google Sheets read-only punch database

```text
Phase 1 の出席判定ロジックを維持したまま、Google Sheets API で打刻データベースを読み取る read-only 機能を追加してください。

要件:
- 読み取り専用
- 前日分だけ取得できる
- 取得データを既存の判定ロジックに渡す
- Salesforce 更新はしない
- Slack 投稿はしない
- dry-run レポートだけ出す
- テストでは Google API をモックする
```

## Phase 3: Salesforce Sandbox read-only

```text
Salesforce Sandbox から研修クラスと参加者を読み取る read-only 機能を追加してください。

要件:
- 本番 Salesforce には接続しない
- Sandbox / dry-run 前提
- オブジェクト名とフィールド名は設定ファイルで差し替え可能にする
- API 接続できない場合でも CSV fixture でテストできるようにする
- README に必要な Salesforce 項目を一覧化する
```

## Phase 4: Slack report preview

```text
出席 dry-run の結果を Slack 投稿用のプレビュー Markdown に整形する機能を作ってください。

要件:
- 本番 Slack には投稿しない
- @channel は使わない
- 管理部確認用の要約を作る
- 出席登録候補、無断欠席候補、確認対象を分ける
- Slack Block Kit に拡張しやすい構造にする
```

## Phase 5: Slack reminder preview

```text
全体リマインド自動投稿の Phase 1 を作ってください。

要件:
- Salesforce または CSV から開催中クラスを取得
- 進捗確認アンケート、打刻リマインド、アーカイブ動画案内の投稿対象を抽出
- Slack 本番投稿はしない
- 投稿文プレビューだけ作る
- 19:30 開始は 19:15、20:00 開始は 19:45 の打刻リマインド対象にする
- テストを追加する
```

## Phase 6: Slack registration check

```text
Slack 登録確認の dry-run を作ってください。

要件:
- Salesforce 参加予定者 CSV と Slack メンバー CSV を照合
- Slack user ID / email を優先して照合
- 氏名のみ一致は確認対象にする
- 未登録者一覧を Markdown と CSV で出力
- Slack 本番 API には接続しない
```

## Phase 7: archive video check preview

```text
アーカイブ動画案内の dry-run を作ってください。

要件:
- 録画一覧 CSV と研修クラス CSV を照合
- 録画ファイル有無、録画 URL、日付、講師、クラスを確認
- Slack 投稿プレビューを作る
- 録画が未確認の場合は投稿候補にしない
- Google Drive の権限変更やファイル移動はしない
```

## Phase 8: withdrawal / retirement checklist

```text
退職・離脱時の解除チェックリストを作ってください。

要件:
- Salesforce 退職/離脱対象 CSV を読み込む
- Slack 解除対象、ICTS AI 解除対象、進捗確認シート更新対象、講師連絡対象を一覧化
- 本人向け連絡文と講師向け連絡文の下書きを作る
- 退職という表現を本人向け文面で使わない設定を持たせる
- 実際の削除・送信・更新はしない
```
