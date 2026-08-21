#!/usr/bin/env python3
"""週次タスク用: 会場・劇団の巡回チェック対象を機械的に算出する。

「たまたま検索でヒットした所だけ確認する」運用だと、頻出会場・頻出劇団を
網羅的にチェックできない。ISO週番号を種にして毎週リストを一定量ずつ
ずらすことで、状態ファイルを持たずに数週間で全件を巡回できるようにする。

会場チェックの目的: そのシーズンの新規公演の有無を確認（新規発見）。
劇団チェックの目的: 既に「よく行く＝好きな劇団」であるものについて、
新作アナウンスをこちらが見落としていないかの確認（新規開拓ではなく漏れ検知）。
次回公演が既にカレンダー登録済みならその劇団はスキップしてよい。

使い方:
    python3 scripts/analyze_trends.py > /tmp/kangeki_trends.json
    python3 scripts/rotation_pick.py /tmp/kangeki_trends.json
"""

import datetime
import json
import sys

VENUES_PER_WEEK = 3
COMPANIES_PER_WEEK = 4


def pick(items, n, week):
    if not items:
        return []
    n = min(n, len(items))
    start = (week * n) % len(items)
    return [items[(start + i) % len(items)] for i in range(n)]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kangeki_trends.json"
    trends = json.loads(open(path, encoding="utf-8").read())
    week = datetime.date.today().isocalendar()[1]

    venues = [v["name"] for v in trends["topVenuesAllTime"]]
    companies = [c["name"] for c in trends["topCompaniesAllTime"]]
    upcoming_companies = set(trends.get("upcomingCompanies", []))

    print(f"ISO week: {week}")
    print()
    print("会場チェック対象（次回ラインナップの有無を確認）:")
    for v in pick(venues, VENUES_PER_WEEK, week):
        print(f"  - {v}")
    print()
    print("劇団チェック対象（新作アナウンス漏れがないか確認。※印は既に今後の公演が登録済み＝軽く確認するだけでよい）:")
    for c in pick(companies, COMPANIES_PER_WEEK, week):
        mark = " ※登録済みあり" if c in upcoming_companies else ""
        print(f"  - {c}{mark}")


if __name__ == "__main__":
    main()
