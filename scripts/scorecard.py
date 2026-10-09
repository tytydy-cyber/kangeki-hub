"""おすすめ提案の採用率を出す。

提案は site/data/proposals.json のgit履歴から全件集め、提案した日より後にカレンダー（events.json）へ
同じ公演が登録されていれば「採用」とみなす。カレンダーへの登録は本人の行動なので、提案が当たったかの代理指標になる。
判定は「劇団名が一致し、かつ演目名の一部が一致する」か「演目名が一致する」。劇団名だけの一致は数えない（同じ劇団の別公演を拾うため）。

Run: python3 scripts/scorecard.py            （Markdownの要約）
     python3 scripts/scorecard.py --json     （週次タスク・集計用）
     python3 scripts/scorecard.py --selftest
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = "site/data/proposals.json"
EVENTS = ROOT / "site/data/events.json"


def norm(s):
    return re.sub(r"[\s　・･\-‐－―~〜「」『』《》【】()（）\"'!！?？:：,，.。、]", "", (s or "")).lower()


def work_of(title, company):
    """「劇団『演目』」形式なら演目、そうでなければ劇団名を除いた残りを演目とみなす。"""
    m = re.search(r"[『「《](.+?)[』」》]", title or "")
    return norm(m.group(1) if m else (title or "").replace(company or "", ""))


def matches(prop, event):
    pw, ew = work_of(prop["title"], prop.get("company")), norm(event.get("work") or event.get("title"))
    same_work = len(pw) >= 2 and len(ew) >= 2 and (pw in ew or ew in pw)
    same_company = norm(prop.get("company")) and norm(prop.get("company")) == norm(event.get("company"))
    return same_work and (same_company or len(pw) >= 4)


def history():
    """(提案日, 提案) を、同じ公演は最初に提案された日で1件にまとめて返す。"""
    log = subprocess.run(["git", "log", "--reverse", "--format=%h %ad", "--date=short", "--", PROPOSALS],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    seen = {}
    for line in filter(None, log):
        sha, day = line.split()
        try:
            data = json.loads(subprocess.run(["git", "show", f"{sha}:{PROPOSALS}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        for section in ("nextMonth", "special"):
            for prop in data.get(section) or []:
                key = norm(prop.get("company")) + "|" + work_of(prop.get("title"), prop.get("company"))
                if key and key not in seen:
                    seen[key] = (day, section, prop)
    return list(seen.values())


def score(proposals, events):
    rows = []
    for day, section, prop in proposals:
        hit = next((e for e in events if (e.get("created") or "") >= day and matches(prop, e)), None)
        rows.append({"proposed": day, "section": section, "title": prop["title"], "source": source_of(prop.get("reason")), "adopted": bool(hit),
                     "registered": hit and hit.get("created")})
    return rows


SOURCES = [("公社流体力学note", r"公社"), ("芸術祭・フェス", r"隕石|五彩|演劇祭|バザール|フェスティバル|芸術祭|フェス"),
           ("頻出劇団の新作", r"頻出|登録済み|過去に登録|再び"), ("戯曲軸", r"戯曲|熱海殺人事件|唐十郎|つかこうへい")]


def source_of(reason):
    """提案理由の文面から、主な情報源を推定する（最初に当たったもの。どれでもなければ「その他」）。"""
    return next((name for name, pattern in SOURCES if re.search(pattern, reason or "")), "その他")


def summary(rows):
    by_month = Counter((r["proposed"][:7], r["adopted"]) for r in rows)
    months = sorted({r["proposed"][:7] for r in rows})
    total, hits = len(rows), sum(r["adopted"] for r in rows)
    return {"total": total, "adopted": hits, "rate": round(hits / total, 3) if total else None,
            "byMonth": [{"month": m, "proposed": by_month[(m, True)] + by_month[(m, False)], "adopted": by_month[(m, True)]} for m in months],
            "bySource": [{"source": src, "proposed": sum(r["source"] == src for r in rows), "adopted": sum(r["adopted"] for r in rows if r["source"] == src)}
                         for src in [n for n, _ in SOURCES] + ["その他"]],
            "adoptedTitles": [r["title"] for r in rows if r["adopted"]]}


def selftest():
    ev = {"title": "新宿梁山泊「下谷万年町物語」", "company": "新宿梁山泊", "work": "下谷万年町物語", "created": "2026-08-01"}
    assert matches({"title": "新宿梁山泊『下谷万年町物語』", "company": "新宿梁山泊"}, ev)
    assert not matches({"title": "新宿梁山泊『少女都市からの呼び声』", "company": "新宿梁山泊"}, ev)  # 同じ劇団の別公演
    assert matches({"title": "『下谷万年町物語』", "company": "別表記の劇団"}, ev)  # 演目名が十分長ければ劇団表記揺れを許す
    rows = score([("2026-08-05", "nextMonth", {"title": "新宿梁山泊『下谷万年町物語』", "company": "新宿梁山泊"})], [ev])
    assert rows[0]["adopted"] is False  # 提案より前に登録済みのものは採用に数えない
    assert source_of("公社流体力学のnoteで紹介") == "公社流体力学note" and source_of("特になし") == "その他"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    events = json.loads(EVENTS.read_text(encoding="utf-8"))["events"]
    rows = score(history(), events)
    s = summary(rows)
    if "--json" in sys.argv:
        print(json.dumps({**s, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        print(f"提案 {s['total']}件のうち、提案後にカレンダー登録 {s['adopted']}件（採用率 {s['rate']:.0%}）")
        for m in s["byMonth"]:
            print(f"- {m['month']}: {m['adopted']}/{m['proposed']}")
        for x in s["bySource"]:
            print(f"- 情報源 {x['source']}: {x['adopted']}/{x['proposed']}")
        print("採用:", "、".join(s["adoptedTitles"]) or "なし")
