#!/usr/bin/env python3
"""松田観劇カレンダーの公開iCalフィードを取得し、site/data/events.json を生成する。

Python 3.9 標準ライブラリのみで動作する。

使い方:
    python3 scripts/build_data.py            # フィードを取得して生成
    python3 scripts/build_data.py --local path/to/basic.ics   # ローカルICSから生成
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FEED_URL = (
    "https://calendar.google.com/calendar/ical/"
    "ooc2a3r5b532knt1472khnrjpg%40group.calendar.google.com/public/basic.ics"
)

JST = timezone(timedelta(hours=9))

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "site" / "data" / "events.json"

URL_RE = re.compile(r"https?://[^\s<>\"]+")
# 「劇団名「作品名」」「劇団名『作品名』」形式の分離（末尾が閉じ括弧のものだけ対象）
TITLE_RE = re.compile(r"^(?P<company>[^「『]+?)\s*(?:「(?P<t1>.+)」|『(?P<t2>.+)』)\s*$")

# 会場名の正規化: Googleカレンダーが英語ローカライズした会場名を日本語の正式表記へ寄せる。
# 集計（上位会場・劇団別）と表示の重複を解消するのが目的。
# 正規化するのは表示用の venue のみで、マップリンクに使う location（住所）は温存するため紐付けは維持される。
# ラテン表記が正式名の会場（SCOOL, BUoY, WOMB 等）は対象外（キーに載せない）。
VENUE_ALIASES = {
    "Hanazono Shrine": "花園神社",
    "The Suzunari": "ザ・スズナリ",
    "Honda Theatre": "本多劇場",
    "Theater 711": "シアター711",
    "Za Kōenji": "座・高円寺",
    "Kichijoji Theatre": "吉祥寺シアター",
    "Oji Theatre": "王子小劇場",
    "Station Square Theater": "駅前劇場",
    "Theater Tram": "シアタートラム",
    "Setagaya Public Theatre": "世田谷パブリックシアター",
    "Asakusa Kyugeki": "浅草九劇",
    "Sengawa Theatre": "調布市せんがわ劇場",
    "Kanagawa Arts Theatre": "KAAT 神奈川芸術劇場",
    "Ueno Storehouse": "上野ストアハウス",
    "Sumida Park Theater Sou": "すみだパークシアター倉",
    "Heaven's Door Company": "三軒茶屋 HEAVEN'S DOOR",
    "Izumo Gallery": "イズモギャラリー",
    "Shinjuku Ganka Art Gallery (Shinjuki Ganka Garō)": "新宿眼科画廊",
    "New National Theatre": "新国立劇場",
    "Parco Theatre": "PARCO劇場",
    "Theatre Cocoon": "シアターコクーン",
    "Mitaka City Arts Center": "三鷹市芸術文化センター",
    "Kinokuniya Hall": "紀伊國屋ホール",
    "Sunshine Theatre": "サンシャイン劇場",
    "Theatre X": "シアターX",
    "Waseda Mini Theatre Drama-Kan": "早稲田小劇場どらま館",
    "Theatre Fushikaden": "シアター風姿花伝",
    "PorePore Higashinakano": "ポレポレ東中野",
    "Shimo-Takaido Cinema": "下高井戸シネマ",
    "Moto Eigakan": "元映画館",
    "Theater Green": "シアターグリーン",
    "Theatre BONBON": "テアトルBONBON",
    "Kamata Onsen": "蒲田温泉",
    "BUoY Cafe & Bar": "BUoY",
    "CLUB CITTA'": "CLUB CITTA'",
    "Club Citta": "CLUB CITTA'",
    "Meiji University Academy Common": "明治大学 アカデミーコモン",
    "Theatre E9 Kyoto": "THEATRE E9 KYOTO",
    "ROHM Theatre Kyoto": "ロームシアター京都",
    "Kyoto Art Center": "京都芸術センター",
    "Aichi Prefectural Art Theater": "愛知県芸術劇場",
    "Tokyo Metropolitan Festival Hall": "東京文化会館",
}


def fetch_ics(local_path=None):
    if local_path:
        return Path(local_path).read_text(encoding="utf-8")
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "kangeki-hub-build"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read().decode("utf-8")


def unfold_lines(text):
    """iCalの行折り返し（継続行は先頭が空白/タブ）を展開する。"""
    lines = []
    for raw in text.splitlines():
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def unescape(value):
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def parse_events(text):
    events = []
    current = None
    for line in unfold_lines(text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key, value = line.split(":", 1)
        name = key.split(";", 1)[0]
        params = key.split(";")[1:]
        if name in ("DTSTART", "DTEND"):
            current[name] = {"value": value, "params": params}
        elif name in ("UID", "SUMMARY", "LOCATION", "DESCRIPTION", "CREATED", "LAST-MODIFIED", "STATUS"):
            current[name] = value
    return events


def to_jst_date(prop):
    """DTSTART/DTENDプロパティをJST基準の日付とall-dayフラグに変換する。"""
    value = prop["value"]
    if "VALUE=DATE" in prop["params"]:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8])), True
    # 時刻付き。フィード上はUTC(Z)のみだが、念のため素の形式も許容する
    dt = datetime.strptime(value.rstrip("Z"), "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        dt = dt.replace(tzinfo=timezone.utc).astimezone(JST)
    return dt.date(), False


# 先頭の注記プレフィックス（（野外）（京都）（映像）（無料）（中止）等）を除去するための正規表現。
# 地域・上演形式・状態の注記であり劇団名の一部ではないため、集計用の company からは外す。
COMPANY_PREFIX_RE = re.compile(r"^(?:[（(][^）)]*[）)]\s*)+")


def strip_company_prefix(name):
    if not name:
        return name
    stripped = COMPANY_PREFIX_RE.sub("", name).strip()
    return stripped or name


def split_title(summary):
    m = TITLE_RE.match(summary)
    if not m:
        return None, None
    company = strip_company_prefix(m.group("company").strip())
    return company, (m.group("t1") or m.group("t2")).strip()


def extract_url_and_note(description):
    m = URL_RE.search(description)
    if not m:
        return None, description.strip() or None
    url = m.group(0)
    note = (description[: m.start()] + description[m.end():]).strip()
    return url, note or None


def build_event(raw):
    summary = unescape(raw.get("SUMMARY", "")).strip()
    if not summary or "DTSTART" not in raw:
        return None

    start, all_day = to_jst_date(raw["DTSTART"])
    if "DTEND" in raw:
        end, end_all_day = to_jst_date(raw["DTEND"])
        # 全日イベントのDTENDは排他的（登録規約の「千秋楽翌日」と一致）
        last_day = end - timedelta(days=1) if end_all_day else end
    else:
        last_day = start
    if last_day < start:
        last_day = start

    # カレンダーへの登録日（嗜好の時系列分析に使う）
    created = None
    if raw.get("CREATED"):
        try:
            created = (
                datetime.strptime(raw["CREATED"].rstrip("Z"), "%Y%m%dT%H%M%S")
                .replace(tzinfo=timezone.utc)
                .astimezone(JST)
                .date()
                .isoformat()
            )
        except ValueError:
            pass

    company, title = split_title(summary)
    url, note = extract_url_and_note(unescape(raw.get("DESCRIPTION", "")))
    location = unescape(raw.get("LOCATION", "")).strip() or None
    # Googleカレンダーの住所付き会場は「会場名, 住所」形式なので先頭部分を会場名とする
    venue = location.split(",", 1)[0].strip() if location else None
    # 英語ローカライズ名を日本語の正式表記へ正規化（locationは温存しマップリンクを維持）
    if venue:
        venue = VENUE_ALIASES.get(venue, venue)

    return {
        "id": raw.get("UID", ""),
        "title": summary,
        "company": company,
        "work": title,
        "start": start.isoformat(),
        "end": last_day.isoformat(),
        "allDay": all_day,
        "created": created,
        "venue": venue,
        "location": location,
        "url": url,
        "note": note,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", help="ローカルのICSファイルパス（指定時はフィードを取得しない）")
    args = parser.parse_args()

    text = fetch_ics(args.local)
    events = [e for e in (build_event(raw) for raw in parse_events(text)) if e]
    events.sort(key=lambda e: (e["start"], e["end"], e["title"]))

    payload = {
        "generatedAt": datetime.now(JST).isoformat(timespec="seconds"),
        "source": FEED_URL,
        "count": len(events),
        "events": events,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    with_url = sum(1 for e in events if e["url"])
    with_company = sum(1 for e in events if e["company"])
    print(f"events: {len(events)}")
    print(f"  with url: {with_url}")
    print(f"  with company/work split: {with_company}")
    print(f"  range: {events[0]['start']} .. {events[-1]['end']}")
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
