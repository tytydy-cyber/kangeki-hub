#!/usr/bin/env python3
"""Check active proposals against each other and the rejection ledger."""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PROPOSALS_PATH = ROOT / "site/data/proposals.json"
REJECTIONS_PATH = ROOT / "data/rejected_proposals.json"


def compact(value):
    """Normalize full-width text and remove separators for loose comparisons."""
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(char for char in value if char.isalnum())


def normalize_url(value):
    parsed = urlsplit(str(value or "").strip())
    host = parsed.netloc.casefold().removeprefix("www.")
    path = re.sub(r"/+", "/", unicodedata.normalize("NFKC", parsed.path)).rstrip("/")
    return host + path


def rejected_match(proposal, rejected):
    same_title = compact(proposal.get("title")) == compact(rejected.get("title"))
    proposal_url, rejected_url = normalize_url(proposal.get("url")), normalize_url(rejected.get("url"))
    proposal_dates, rejected_dates = compact(proposal.get("dates")), compact(rejected.get("dates"))
    same_url = bool(proposal_url and rejected_url and proposal_url == rejected_url)
    same_dates = bool(proposal_dates and rejected_dates and proposal_dates == rejected_dates)
    return same_title and (same_url or same_dates)


def validate(proposals, rejections):
    errors = []
    if not isinstance(rejections, list):
        return ["rejection ledger must be an array"]
    valid_rejections = []
    for index, rejected in enumerate(rejections, 1):
        if not isinstance(rejected, dict) or not all(rejected.get(key) for key in ("title", "dates", "url", "rejectedAt")):
            errors.append(f"rejections[{index}] must have title, dates, url and rejectedAt")
            continue
        valid_rejections.append(rejected)
    seen = {}
    seen_urls = {}
    for section in ("nextMonth", "special"):
        items = proposals.get(section, [])
        if not isinstance(items, list):
            errors.append(f"{section} must be an array")
            continue
        for index, item in enumerate(items, 1):
            if not isinstance(item, dict):
                errors.append(f"{section}[{index}] must be an object")
                continue
            title = compact(item.get("title"))
            if not title:
                errors.append(f"{section}[{index}] has no title")
                continue
            if not item.get("dates") or not item.get("url"):
                errors.append(f"{section}[{index}] must have dates and url")
            if title in seen:
                errors.append(
                    f"duplicate proposal title: {item.get('title')} "
                    f"({seen[title]} and {section}[{index}])"
                )
            else:
                seen[title] = f"{section}[{index}]"
            url = normalize_url(item.get("url"))
            if url:
                if url in seen_urls:
                    errors.append(
                        f"duplicate proposal URL: {item.get('url')} "
                        f"({seen_urls[url]} and {section}[{index}])"
                    )
                else:
                    seen_urls[url] = f"{section}[{index}]"
            for rejected in valid_rejections:
                if rejected_match(item, rejected):
                    errors.append(
                        f"rejected proposal is active again: {item.get('title')} "
                        f"({section}[{index}], rejected {rejected.get('rejectedAt')})"
                    )
                    break
    return errors


def selftest():
    rejected = {
        "title": "舞台芸術祭『秋の隕石2026東京』",
        "dates": "10/9(金) 〜 11/3(火祝)",
        "url": "https://www.geigeki.jp/performance/theater415/",
        "rejectedAt": "2026-10-14",
    }
    same_performance = {
        "title": "舞台芸術祭「秋の隕石2026東京」",
        "dates": "10/9（金）〜11/3（火祝）",
        "url": "https://geigeki.jp/performance/theater415",
    }
    revival = {
        "title": same_performance["title"],
        "dates": "2027/10/08〜2027/11/02",
        "url": "https://geigeki.jp/performance/theater415-2027",
    }
    assert rejected_match(same_performance, rejected)
    assert not rejected_match(revival, rejected)
    assert not rejected_match({"title": rejected["title"]}, {"title": rejected["title"]})
    assert validate({"nextMonth": [same_performance], "special": []}, [rejected])
    assert not validate({"nextMonth": [revival], "special": []}, [rejected])
    assert any("duplicate" in error for error in validate({"nextMonth": [revival], "special": [revival]}, [rejected]))
    different_title_same_url = {**revival, "title": "別の公演"}
    assert any(
        "duplicate proposal URL" in error
        for error in validate({"nextMonth": [revival], "special": [different_title_same_url]}, [])
    )
    print("selftest: OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run normalization assertions")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0

    try:
        proposals = json.loads(PROPOSALS_PATH.read_text(encoding="utf-8"))
        rejections = json.loads(REJECTIONS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    errors = validate(proposals, rejections)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    active_count = len(proposals.get("nextMonth", [])) + len(proposals.get("special", []))
    print(f"proposals: OK ({active_count} active, {len(rejections)} rejected records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
