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

2. 会場名・劇団名の表記揺れ保守（正規化の維持）
   - 会場名: events.json に「英語ローカライズ表記なのに `scripts/build_data.py` の `VENUE_ALIASES` に無い会場」が新たに出ていないか確認。日本語の正式名が明確なものだけ `VENUE_ALIASES` に追記（ラテン表記が正式名の会場 SCOOL/BUoY/WOMB 等は対象外）
   - 劇団名: 同じ劇団が別表記で分かれていないか確認し、`COMPANY_ALIASES`（build_data.py）で**メジャーな呼び方**へ寄せる。見つけ方の例:
     - `python3 scripts/analyze_trends.py` の topCompanies/一覧で、略称と正式名（例: ゴキコン↔ゴキブリコンビナート）、「劇団」有無（例: 不労社↔劇団不労社）、別公演名（例: 唐組若手公演↔唐組）などの重複を探す
     - 部分文字列で片方がもう片方に含まれるペアは有力候補
   - **同一劇団だと確実に言えるものだけ**追記する。コラボ「A×B」、大学の別企画（卒業公演/プロジェクト）、別劇団は統合しない。迷うものは触らない
   - VENUE_ALIASES / COMPANY_ALIASES を追記したら build_data.py を再実行

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

5. 劇団概要の追記（site/data/companies.json）
   - `companies.json` の `companies` に概要が無い劇団のうち、登録数が多い or 今後の公演がある劇団を **3〜5件** 選ぶ
   - 各劇団を Web 検索し、公式サイト等の公開情報から2〜4文の概要を書く（主宰・結成年・拠点・作風など、確認できた事実のみ。憶測は書かない）
   - `{ "劇団名": {"summary": "...", "url": "<出典>", "updatedAt": "<当日>"} }` の形で追記。キーは events.json の company と完全一致させる（プレフィックス除去後の表記）
   - 情報が乏しく確実なことが書けない劇団は飛ばす（無理に埋めない）
   - トップの `generatedAt` を当日に更新
   - 一度に全劇団を埋めようとせず、毎週少しずつ拡充する

6. コミットとデプロイ
   ```
   git add -A
   git commit -m "Weekly update: proposals, digest, company overviews (<当日>)"
   git push origin main
   ```
   push で GitHub Actions が自動デプロイする。

## 注意

- カレンダー本体（events.json）は Actions がフィードから毎日再生成するので commit しない（.gitignore 済み）
- 嗜好プロファイルはリポジトリに個人情報を置かない方針。傾向は events.json の集計から都度導く
- 提案は「未登録のもの」に限る。既にカレンダーにある公演は提案しない
