# kangeki-hub

観劇・イベント・飲食の記録を集約し、静的サイトとして公開するプロジェクト。設計の全体像は [docs/DESIGN.md](docs/DESIGN.md) を参照。

## スコープ

- 対象: 観劇 + イベント全般
- 対象外: 飲食店（P2以降で別途検討。現時点でこのリポジトリのコードは触らない）

## 観劇カレンダー

- カレンダーID: `ooc2a3r5b532knt1472khnrjpg@group.calendar.google.com`（確認済み）
- 公開iCalフィード: `https://calendar.google.com/calendar/ical/ooc2a3r5b532knt1472khnrjpg%40group.calendar.google.com/public/basic.ics`
- タイムゾーン: Asia/Tokyo（確認済み）
- カレンダーの意味: 確定予定や観劇記録ではなく「見込まれる公演」のみを登録している。サイト上の表現もこれに合わせる
- 既存の登録規約:
  - 終日イベント形式で登録する（時刻付きイベントも一部混在）
  - 終了日は「千秋楽の翌日」を設定する（iCalの排他的DTENDと一致）

## Notion

- InboxページID: `393020b1f16781fbab1bf6ec16b8a3b1`
- 観劇DB / イベントDB / 飲食DB のデータベースIDはP2で確定次第ここに追記する

## 出力規約

- アスタリスク（`*`）は使用しない
- TODO: 他に既存チャットでの出力規約があれば追記

## 傾向ダイジェスト（digest.html / data/digest.json）

年次など広範囲の傾向分析ページ（提案は載せない）。生成手順:
1. `python3 scripts/build_data.py && python3 scripts/analyze_trends.py > /tmp/trends.json`
2. trends.json から digest.json を生成（年別件数・開催月分布・上位劇団/会場・直近180日の劇団）。`generatedAt` を当日に
3. digest.js が横棒グラフ（bars）とランキング（ranklist）で描画

## おすすめ提案（proposals.html / data/proposals.json）

ダイジェストとは別ページ。2セクション構成:
- `nextMonth`: 今日から約1ヶ月の範囲で「カレンダー未登録」かつ嗜好傾向に近い公演。頻出会場のスケジュール（例: 本多劇場グループのスズナリ欄）や頻出劇団の公式が有力な情報源
- `special`: 期間を問わず特筆すべき公演（遠征・早期完売が見込まれるもの等）。任意

登録済みと重複させないため、analyze_trends.py の `upcomingTitles` を必ず突き合わせる。生成後 commit → push（Actionsが自動デプロイ）。

定期化（scheduled task）は内容確認後に判断（初回は2026-07-15に手動生成）。

## 既知のデータ品質課題

- 会場名にGoogleカレンダー由来の英語表記が混入（例: 花園神社 と "Hanazono Shrine"、"Kanagawa Arts Theatre" が別集計）。build_data.py 側で会場名の正規化を入れると集計・マップリンク・劇団別の精度が上がる（未対応）

## 開発メモ

- データ生成: `python3 scripts/build_data.py`（`--local <ics>` でローカルファイルから）。出力は `site/data/events.json`（.gitignore対象、デプロイ時にActionsが生成）
- 傾向分析: `python3 scripts/analyze_trends.py`（events.jsonを読んでJSONを標準出力へ）
- ローカル確認: `cd site && python3 -m http.server 8765`
- ビルドはPython 3.9標準ライブラリのみ。Node.jsや外部パッケージは使わない（この環境に未導入のため）
- Claude Codeのプレビューツール（preview_start）はDesktop配下に直接アクセスできない。site/をスクラッチパッドにコピーし、getcwd()を呼ばないサーバースクリプト経由で配信する方式で回避した実績あり

## 公開方針（確定）

- サイト・リポジトリとも完全公開。個人情報（生活圏・食の除外項目など）はリポジトリにcommitしない
- 過去の観劇アーカイブもサイトに表示する
- 週次推薦はClaude Codeのscheduled taskで実行（GitHub ActionsからのAPI直接呼び出しはしない）

## 現在のフェーズ

- [x] P1: 観劇カレンダー（iCalフィード）→ 静的サイト。公開済み（2026-07-12）: https://tytydy-cyber.github.io/kangeki-hub/
- [ ] P2: Notion DB 3本設計 + 飲食データ取り込み
- [ ] P3: 週次推薦バッチ + メール配信
- [ ] P4: イベント全般の運用定着、マップビュー

着手前に [docs/DESIGN.md](docs/DESIGN.md) の「未確定事項」を埋めること。
