#!/usr/bin/env python3
"""Render data/contributions.json as an animated SVG contribution heatmap.

A classic 53-week x 7-day calendar of rounded, colored boxes. Reveals once
with a diagonal, box-by-box slide-down (CSS keyframes on load, then freeze),
plus a Less->More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
WEEKS = 53
PAD = 20
FOOTER_H = 40
W = WEEKS * (CELL + GAP) + PAD * 2
H = 7 * (CELL + GAP) + PAD * 2 + FOOTER_H

BG = "#0d1117"
FG = "#c9d1d9"
DIM = "#8b949e"


def load_data() -> dict:
    src = DATA / "contributions.json"
    if not src.exists():
        print(f"Run fetch_contributions.py first — missing {src}")
        raise SystemExit(1)
    return json.loads(src.read_text())


def align_days(days: list[list]) -> dict:
    """Map each ISO date string to a level 0..5."""
    return {d: min(lvl, 5) for d, lvl in days}


def month_labels() -> list[tuple[int, str]]:
    """Return (column_index, month_abbr) for the grid header."""
    labels = []
    start = date.today() - timedelta(weeks=WEEKS - 7, days=date.today().weekday())
    # Align so the grid covers a full year window ending with today's week.
    cursor = start.replace(day=1)
    last = None
    while cursor <= date.today():
        if cursor.month != last:
            col = ((cursor - start).days // 7)
            labels.append((col, cursor.strftime("%b")))
            last = cursor.month
        cursor += timedelta(days=1)
    return labels


def build_svg(payload: dict) -> str:
    level_map = align_days(payload["days"])
    stats = payload["stats"]

    # Build a 53-week x 7-day grid ending at the most recent Thursday-ish
    # week used by GitHub (last day of the grid = today).
    today = date.today()
    # Monday-based start of the current week.
    week_start = today - timedelta(days=today.weekday())
    start = week_start - timedelta(weeks=WEEKS - 1)

    cells = []
    for w in range(WEEKS):
        for d in range(7):
            day = start + timedelta(weeks=w, days=d)
            if day > today:
                continue
            lvl = level_map.get(day.isoformat(), 0)
            x = PAD + w * (CELL + GAP)
            y = PAD + 20 + d * (CELL + GAP)  # +20 for month header
            color = PALETTE[lvl]
            cells.append((x, y, color, day.isoformat()))

    # Diagonal reveal: stagger each cell by (week + day) so boxes slide in
    # diagonally, then freeze.
    order = sorted(cells, key=lambda c: c[0] + c[1])
    diag_time = 0.02

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
        f'height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="12"/>',
    ]

    # Month labels.
    for col, label in month_labels():
        x = PAD + col * (CELL + GAP)
        parts.append(
            f'<text x="{x}" y="{PAD + 10}" font-family="monospace" '
            f'font-size="11" fill="{DIM}">{label}</text>'
        )

    # Cells, each a rounded rect that drops in diagonally once.
    for i, (x, y, color, _iso) in enumerate(order):
        begin = round(i * diag_time, 3)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{color}">'
            f'<animate attributeName="y" from="{y - 6}" to="{y}" '
            f'begin="{begin}s" dur="0.35s" fill="freeze"/>'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin}s" dur="0.35s" fill="freeze"/>'
            f'</rect>'
        )

    # Legend (Less -> More).
    legend_y = H - FOOTER_H + 24
    parts.append(
        f'<text x="{PAD}" y="{legend_y}" font-family="monospace" '
        f'font-size="12" fill="{DIM}">Less</text>'
    )
    lx = PAD + 46
    for color in PALETTE:
        parts.append(
            f'<rect x="{lx}" y="{legend_y - 9}" width="11" height="11" '
            f'rx="2" fill="{color}"/>'
        )
        lx += 15
    parts.append(
        f'<text x="{lx}" y="{legend_y}" font-family="monospace" '
        f'font-size="12" fill="{DIM}">More</text>'
    )

    # Stats footer.
    parts.append(
        f'<text x="{W - PAD}" y="{legend_y}" text-anchor="end" '
        f'font-family="monospace" font-size="12" fill="{FG}">'
        f'{stats["total"]:,} contributions · '
        f'current streak {stats["current_streak"]}d · '
        f'longest {stats["longest_streak"]}d · '
        f'best day {stats["best_day"]}'
        f'</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    payload = load_data()
    OUT.write_text(build_svg(payload))
    print(f"Wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
