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


def top(counter, n):
    return [{"name": k, "count": v} for k, v in counter.most_common(n)]


def company_counts(evs):
    """劇団の件数を公演単位で数える。"""
    seen = {}
    for e in evs:
        if not e.get("company"):
            continue
        seen.setdefault(e["company"], set()).add(e.get("production") or e.get("title"))
    return Counter({name: len(prods) for name, prods in seen.items()})


def production_count(evs):
    return len({e.get("production") or (e.get("company"), e.get("title"), e.get("start")) for e in evs})


def build_digest(events, today):
    """登録行動の直近90日を、その前の90日と比較する月次ダイジェスト。"""
    current_start = (today - timedelta(days=89)).isoformat()
    previous_start = (today - timedelta(days=179)).isoformat()
    current = [e for e in events if current_start <= (e.get("created") or "") <= today.isoformat()]
    previous = [e for e in events if previous_start <= (e.get("created") or "") < current_start]
    older = [e for e in events if (e.get("created") or "") < current_start]
    upcoming = [e for e in events if e["end"] >= today.isoformat()]

    current_companies = company_counts(current)
    previous_companies = company_counts(previous)
    older_companies = set(company_counts(older))
    discoveries = sorted(
        (e for e in current_companies if e not in older_companies),
        key=lambda name: current_companies[name],
        reverse=True,
    )
    returning = [name for name in current_companies if name in older_companies]
    momentum = [
        {
            "name": name,
            "current": count,
            "previous": previous_companies.get(name, 0),
            "delta": count - previous_companies.get(name, 0),
        }
        for name, count in current_companies.items()
        if count > previous_companies.get(name, 0)
    ]
    momentum.sort(key=lambda row: (-row["delta"], -row["current"], row["name"]))

    pace_start = (today - timedelta(days=365)).isoformat()
    pace_events = [e for e in events if (e.get("created") or "") >= pace_start]
    pace_by_production = {}
    for e in pace_events:
        key = e.get("production") or (e.get("company"), e.get("title"), e.get("start"))
        created = e.get("created")
        if created and (key not in pace_by_production or created < pace_by_production[key]):
            pace_by_production[key] = created
    pace = Counter(created[:7] for created in pace_by_production.values())
    current_productions = production_count(current)
    previous_productions = production_count(previous)

    return {
        "generatedAt": today.isoformat(),
        "cadence": "月次更新（毎月最初の金曜）",
        "window": {"days": 90, "from": current_start, "to": today.isoformat()},
        "overview": {
            "stats": [
                {"label": "直近90日の新規登録", "value": f"{current_productions}公演"},
                {"label": "前の90日との差", "value": f"{current_productions - previous_productions:+d}公演"},
                {"label": "初登場の団体", "value": f"{len(discoveries)}団体"},
                {"label": "継続して追う団体", "value": f"{len(returning)}団体"},
            ],
            "text": "鑑賞実績ではなく、カレンダーへ何を登録したかを分析。直近90日を前の90日と比べ、関心の広がりと継続を捉える。",
        },
        "comparison": {
            "current": current_productions,
            "previous": previous_productions,
            "currentLabel": f"{current_start}〜{today.isoformat()}",
            "previousLabel": f"{previous_start}〜{(today - timedelta(days=90)).isoformat()}",
        },
        "registrationPace": [
            {"month": month, "count": count} for month, count in sorted(pace.items())
        ],
        "momentum": momentum[:10],
        "discoveries": [
            {"name": name, "count": current_companies[name]} for name in discoveries[:12]
        ],
        "recentTop": top(company_counts(pace_events), 12),
        "upcomingCount": len(upcoming),
        "notes": "Googleカレンダーへの登録日を基準に公演単位で集計。登録は興味・把握を示すもので、実際の鑑賞数や評価ではない。",
    }


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    events = data["events"]
    today_date = datetime.now(JST).date()
    today = today_date.isoformat()
    recent_cutoff = (datetime.now(JST).date() - timedelta(days=180)).isoformat()

    upcoming = [e for e in events if e["end"] >= today]
    recent = [e for e in events if e.get("created") and e["created"] >= recent_cutoff]

    if "--digest" in sys.argv or "--write-digest" in sys.argv:
        digest = json.dumps(build_digest(events, today_date), ensure_ascii=False, indent=1) + "\n"
        if "--write-digest" in sys.argv:
            (DATA_PATH.parent / "digest.json").write_text(digest, encoding="utf-8")
        else:
            print(digest, end="")
        return

    companies_all = company_counts(events)
    companies_recent = company_counts(recent)
    venues_all = Counter(e["venue"] for e in events if e["venue"])
    venues_recent = Counter(e["venue"] for e in recent if e["venue"])

    # 年別（開催年ベース）の集計: 件数・上位劇団（公演単位）・上位会場
    by_year = {}
    years = sorted({e["start"][:4] for e in events})
    for y in years:
        ye = [e for e in events if e["start"][:4] == y]
        by_year[y] = {
            "count": len(ye),
            "topCompanies": top(company_counts(ye), 5),
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
    if "--selftest" in sys.argv:
        sample = [
            {"title": "A", "company": "新規", "production": 1, "start": "2026-10-01", "end": "2026-10-02", "created": "2026-10-01"},
            {"title": "B", "company": "継続", "production": 2, "start": "2026-10-03", "end": "2026-10-04", "created": "2026-09-01"},
            {"title": "C", "company": "継続", "production": 3, "start": "2026-01-01", "end": "2026-01-02", "created": "2026-01-01"},
        ]
        digest = build_digest(sample, datetime(2026, 10, 12).date())
        assert digest["overview"]["stats"][0]["value"] == "2公演"
        assert digest["overview"]["stats"][2]["value"] == "1団体"
        assert digest["overview"]["stats"][3]["value"] == "1団体"
        print("selftest ok")
    else:
        main()
