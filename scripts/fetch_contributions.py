#!/usr/bin/env python3
"""Fetch the user's public contribution calendar — no token required.

GitHub serves the contribution calendar as public HTML at
https://github.com/users/<username>/contributions. Parse the day cells
with BeautifulSoup and write data/contributions.json with raw days plus
derived stats.

Usage:
    python scripts/fetch_contributions.py [username]
"""
import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "imzyrix"
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_days() -> list[tuple[str, int]]:
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    for td in soup.select("td[data-date]"):
        date = td["data-date"]
        count = int(td.get("data-level", "0"))
        days.append((date, count))
    return days


def derive_stats(days: list[tuple[str, int]]) -> dict:
    counts = [c for _, c in days]
    total = sum(counts)

    current, longest = 0, 0
    run = 0
    c_run = 0
    for c in counts:
        if c > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # Current streak from the most recent day backwards.
    for c in reversed(counts):
        if c > 0:
            c_run += 1
        else:
            break
    current = c_run

    best_day = max(counts) if counts else 0
    monthly: dict[str, int] = {}
    for date, c in days:
        monthly[date[:7]] = monthly.get(date[:7], 0) + c

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": dict(sorted(monthly.items())),
    }


def main() -> None:
    days = fetch_days()
    stats = derive_stats(days)
    payload = {
        "username": USERNAME,
        "days": days,
        "stats": stats,
    }
    out = DATA / "contributions.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out}: {len(days)} days, {stats['total']} contributions")


if __name__ == "__main__":
    main()
