#!/usr/bin/env python3
"""予約情報JSONの形式とカレンダーUIDとの対応を検査する。"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
TICKETING = ROOT / "site" / "data" / "ticketing.json"
EVENTS = ROOT / "site" / "data" / "events.json"
STATUSES = {"sold-out", "cancelled"}


def parse_datetime(value, field):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ValueError(f"{field}: ISO 8601形式ではありません")
    if "T" in value and parsed.tzinfo is None:
        raise ValueError(f"{field}: 時刻を入れる場合はタイムゾーンも必要です")
    if "T" not in value:
        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=9)))
    return parsed


def validate(data, event_ids):
    errors = []
    seen_ids = set()
    try:
        datetime.fromisoformat(data.get("generatedAt", ""))
    except (TypeError, ValueError):
        errors.append("generatedAt: ISO日付が必要です")
    if not isinstance(data.get("items"), list):
        return ["items: 配列が必要です"]
    for i, item in enumerate(data["items"]):
        prefix = f"items[{i}]"
        ids = item.get("eventIds")
        if not isinstance(ids, list) or not ids or not all(isinstance(v, str) and v for v in ids):
            errors.append(f"{prefix}.eventIds: 1件以上の文字列が必要です")
            ids = []
        for event_id in ids:
            if event_id in seen_ids:
                errors.append(f"{prefix}.eventIds: UIDが重複しています: {event_id}")
            seen_ids.add(event_id)
            if event_ids is not None and event_id not in event_ids:
                errors.append(f"{prefix}.eventIds: events.jsonに無いUIDです: {event_id}")
        if not item.get("title") or not item.get("checkedAt"):
            errors.append(f"{prefix}: titleとcheckedAtが必要です")
        else:
            try:
                datetime.fromisoformat(item["checkedAt"])
            except (TypeError, ValueError):
                errors.append(f"{prefix}.checkedAt: ISO日付が必要です")
        stages = item.get("stages")
        if not isinstance(stages, list) or not stages:
            errors.append(f"{prefix}.stages: 1件以上必要です")
            continue
        for j, stage in enumerate(stages):
            sp = f"{prefix}.stages[{j}]"
            if not stage.get("label"):
                errors.append(f"{sp}.label: 必須です")
            status = stage.get("status")
            if status and status not in STATUSES:
                errors.append(f"{sp}.status: 未対応です: {status}")
            opened = None
            if stage.get("opensAt"):
                try:
                    opened = parse_datetime(stage["opensAt"], f"{sp}.opensAt")
                except ValueError as exc:
                    errors.append(str(exc))
            elif not status:
                errors.append(f"{sp}: opensAtまたはstatusが必要です")
            if stage.get("closesAt"):
                try:
                    closed = parse_datetime(stage["closesAt"], f"{sp}.closesAt")
                    if "T" not in stage["closesAt"]:
                        closed += timedelta(days=1)
                    if opened and closed <= opened:
                        errors.append(f"{sp}.closesAt: opensAtより後にしてください")
                except ValueError as exc:
                    errors.append(str(exc))
            url = stage.get("url")
            parsed_url = urlparse(url) if url else None
            if url and (parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc):
                errors.append(f"{sp}.url: http(s) URLが必要です")
    return errors


def selftest():
    valid = {
        "generatedAt": "2026-10-12",
        "items": [{
            "eventIds": ["uid"], "title": "公演", "checkedAt": "2026-10-12",
            "stages": [
                {"label": "先行", "opensAt": "2026-10-13T10:00:00+09:00", "closesAt": "2026-10-14T18:00:00+09:00"},
                {"label": "一般", "status": "sold-out"},
            ],
        }]
    }
    assert validate(valid, {"uid"}) == []
    invalid = json.loads(json.dumps(valid))
    invalid["items"][0]["stages"][0]["closesAt"] = "2026-10-12T18:00:00+09:00"
    assert validate(invalid, {"uid"})
    invalid = json.loads(json.dumps(valid))
    invalid["items"][0]["stages"][1]["status"] = "open"
    assert validate(invalid, {"uid"})
    print("selftest: ok")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    data = json.loads(TICKETING.read_text(encoding="utf-8"))
    event_ids = None
    if EVENTS.exists():
        event_data = json.loads(EVENTS.read_text(encoding="utf-8"))
        event_ids = {event["id"] for event in event_data["events"]}
    errors = validate(data, event_ids)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"ticketing: {len(data['items'])}公演 / {sum(len(i['stages']) for i in data['items'])}受付")
    return 0


if __name__ == "__main__":
    sys.exit(main())
