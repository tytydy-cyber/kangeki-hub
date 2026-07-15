# 週次自動タスク手順（毎週金曜0時）

おすすめ提案（proposals.json）の更新と、傾向ダイジェスト・会場名の保守を行う。
このファイルは定期タスクが参照する正の手順書。手順を変えたらここを更新する。

## 実行環境

- 対象リポジトリ: `/Users/tytydy/Desktop/Claudecode/kangeki-hub`
- `gh` は `~/.local/bin` にある（PATHに追加済み）
- Python 3 標準ライブラリのみ。追加インストール不要

## 手順

1. 最新化とデータ生成
   ```
   cd /Users/tytydy/Desktop/Claudecode/kangeki-hub
   git pull --ff-only
   python3 scripts/build_data.py
   python3 scripts/analyze_trends.py > /tmp/kangeki_trends.json
   ```

2. 会場名の保守（正規化の維持）
   - events.json に「英語ローカライズ表記なのに `scripts/build_data.py` の `VENUE_ALIASES` に無い会場」が新たに出ていないか確認する
   - 日本語の正式名が明確なものだけ `VENUE_ALIASES` に追記（ラテン表記が正式名の会場 SCOOL/BUoY/WOMB 等は対象外）。判断に迷うものは触らない
   - 追記したら build_data.py を再実行

3. ダイジェスト更新（digest.json）
   - `/tmp/kangeki_trends.json` を基に `site/data/digest.json` を再生成（年別件数・開催月分布・上位劇団/会場・直近180日の劇団・`generatedAt`=当日）
   - スキーマは現行 digest.json に合わせる

4. おすすめ提案更新（proposals.json）
   - `window` を「今日 〜 約1ヶ月後」に設定
   - `analyze_trends.py` の `upcomingCompanies` / `upcomingTitles` で登録済みを把握し、**重複を避ける**
   - `nextMonth`: 今日から約1ヶ月で「カレンダー未登録」かつ嗜好傾向（アングラ・小劇場・テント芝居・舞踏、頻出劇団・頻出会場）に近い公演を2〜5件。Web検索と公式/劇場スケジュール（例: 本多劇場グループのスズナリ欄）で日程・会場・URLを確認
   - `special`: 期間を問わず特筆すべき公演（遠征・早期完売が見込まれるもの等）があれば。無ければ空配列
   - 各項目に `reason`（なぜ嗜好に合うか、登録済みとどう違うか）を書く
   - `generatedAt` を当日に

5. コミットとデプロイ
   ```
   git add -A
   git commit -m "Weekly update: proposals and digest (<当日>)"
   git push origin main
   ```
   push で GitHub Actions が自動デプロイする。

## 注意

- カレンダー本体（events.json）は Actions がフィードから毎日再生成するので commit しない（.gitignore 済み）
- 嗜好プロファイルはリポジトリに個人情報を置かない方針。傾向は events.json の集計から都度導く
- 提案は「未登録のもの」に限る。既にカレンダーにある公演は提案しない
