#!/usr/bin/env python3
"""site/data/events.json から嗜好傾向を集計してJSONで出力する。

ダイジェスト（年次など広範囲の傾向）と提案（直近の未登録候補選定）の
両方の入力に使う。Python 3.9 標準ライブラリのみ。

使い方:
    python3 scripts/build_data.py && python3 scripts/analyze_trends.py
"""

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
DATA_PATH = Path(__file__).resolve().parent.parent / "site" / "data" / "events.json"


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    events = data["events"]
    today = datetime.now(JST).date().isoformat()
    recent_cutoff = (datetime.now(JST).date() - timedelta(days=180)).isoformat()

    upcoming = [e for e in events if e["end"] >= today]
    recent = [e for e in events if e.get("created") and e["created"] >= recent_cutoff]

    def top(counter, n):
        return [{"name": k, "count": v} for k, v in counter.most_common(n)]

    companies_all = Counter(e["company"] for e in events if e["company"])
    companies_recent = Counter(e["company"] for e in recent if e["company"])
    venues_all = Counter(e["venue"] for e in events if e["venue"])
    venues_recent = Counter(e["venue"] for e in recent if e["venue"])

    # 年別（開催年ベース）の集計: 件数・上位劇団・上位会場
    by_year = {}
    years = sorted({e["start"][:4] for e in events})
    for y in years:
        ye = [e for e in events if e["start"][:4] == y]
        by_year[y] = {
            "count": len(ye),
            "topCompanies": top(Counter(e["company"] for e in ye if e["company"]), 5),
            "topVenues": top(Counter(e["venue"] for e in ye if e["venue"]), 5),
        }

    # 開催月の分布（季節性: どの月に観劇が多いか、年を通算）
    month_hist = Counter(int(e["start"][5:7]) for e in events)
    months = {str(m): month_hist.get(m, 0) for m in range(1, 13)}

    # 直近12ヶ月の登録ペース（created基準）
    pace = Counter(
        e["created"][:7]
        for e in events
        if e.get("created")
        and e["created"] >= (datetime.now(JST).date() - timedelta(days=365)).isoformat()
    )

    result = {
        "today": today,
        "total": len(events),
        "upcomingCount": len(upcoming),
        "yearsCovered": [years[0], years[-1]] if years else [],
        "recentWindowDays": 180,
        "recentCount": len(recent),
        "byYear": by_year,
        "monthHistogram": months,
        "topCompaniesAllTime": top(companies_all, 25),
        "topCompaniesRecent": top(companies_recent, 20),
        "topVenuesAllTime": top(venues_all, 20),
        "topVenuesRecent": top(venues_recent, 10),
        "registrationPaceByMonth": dict(sorted(pace.items())),
        "upcomingCompanies": sorted({e["company"] for e in upcoming if e["company"]}),
        "upcomingTitles": [
            {"title": e["title"], "start": e["start"], "end": e["end"]} for e in upcoming
        ],
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
