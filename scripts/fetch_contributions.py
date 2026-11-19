#!/usr/bin/env python3
"""Fetch the last year of GitHub contributions for misbahulhaq09 and rewrite
data/contributions.json in the local schema used by render_readme_cards.py.

Source API: https://github-contributions-api.jogruber.de/v4/<user>?y=last
Stdlib only. On ANY failure (network, HTTP, bad JSON, schema mismatch) the
script exits non-zero and leaves the existing data file untouched.
"""
import json
import os
import sys
import urllib.request

USER = "misbahulhaq09"
URL = f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "contributions.json")


def level_for(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 4:
        return 2
    if count <= 6:
        return 3
    return 4


def main() -> int:
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "github-profile-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                print(f"fetch failed: HTTP {resp.status}", file=sys.stderr)
                return 1
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # network, decode, JSON errors
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 1

    try:
        raw_days = payload["contributions"]
        total = int(payload["total"]["lastYear"])
        days = []
        for item in raw_days:
            count = int(item["count"])
            days.append({
                "date": str(item["date"]),
                # Recompute level with our scale so the cards stay consistent
                # even if the upstream level buckets ever change.
                "count": count,
                "level": level_for(count),
            })
        days.sort(key=lambda d: d["date"])
        if not days:
            raise ValueError("empty contributions list")
        if sum(d["count"] for d in days) != total:
            # Trust the per-day data; keep the reported total only if it agrees.
            total = sum(d["count"] for d in days)
    except Exception as exc:
        print(f"bad payload: {exc}", file=sys.stderr)
        return 1

    out = {"total": {"lastYear": total}, "contributions": days}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    os.replace(tmp, OUT)  # atomic: old file survives any failure above
    print(f"wrote {OUT}: {len(days)} days, total {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
