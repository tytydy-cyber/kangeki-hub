#!/usr/bin/env python3
"""site/data/events.json から嗜好傾向を集計してJSONで出力する。

週次ダイジェスト生成の入力に使う。Python 3.9 標準ライブラリのみ。

使い方:
    python3 scripts/build_data.py && python3 scripts/analyze_trends.py
"""

import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
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

    # 直近12ヶ月の登録ペース（created基準）
    pace = Counter(
        e["created"][:7] for e in events if e.get("created") and e["created"] >= (
            datetime.now(JST).date() - timedelta(days=365)
        ).isoformat()
    )

    result = {
        "today": today,
        "total": len(events),
        "upcomingCount": len(upcoming),
        "recentWindowDays": 180,
        "recentCount": len(recent),
        "topCompaniesAllTime": top(companies_all, 20),
        "topCompaniesRecent": top(companies_recent, 20),
        "topVenuesAllTime": top(venues_all, 15),
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
