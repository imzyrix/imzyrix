"""
Render a professional dark-terminal activity panel from
data/contributions.json.

A single self-contained SVG (no JS) that reveals on load and freezes, so
GitHub's sandboxed <img> rendering plays it. Components:

  - terminal titlebar (traffic lights + ./activity.sh) + subtitle bar
  - animated monthly contribution bar chart (last 12 months)
  - stat cards row: total, current streak, longest streak, best day
  - weekday heat row: which days of the week you commit on
  - legend + footer status bar with a steady blinking cursor

Usage:
    python scripts/make_activity_svg.py     # writes activity.svg

Run by .github/workflows/update-profile-art.yml from the same data as the
contribution heatmap, so both stay in sync.
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "activity.svg")

# ---- palette (matches the rest of the profile) -----------------------------
BG = "#0a0e14"
BG2 = "#0d1420"
FRAME = "#1f6feb"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#58a6ff"
GREEN = "#39d353"
GOLD = "#f2cc60"
RED = "#f85149"
INK = "#c9d1d9"

# ---- layout ---------------------------------------------------------------
W = 980
H = 610
TITLEBAR_H = 32
SUBTITLE_H = 30
PAD = 18

CHART_TOP = TITLEBAR_H + SUBTITLE_H + PAD
CHART_H = 210
CHART_LEFT = PAD + 34
CHART_W = W - PAD * 2 - 34

CARDS_TOP = CHART_TOP + CHART_H + 40
CARD_W = (W - PAD * 2 - 3 * 12) // 4
CARD_H = 92

WEEK_TOP = CARDS_TOP + CARD_H + 36
FOOTER_H = 34
FOOTER_TOP = WEEK_TOP + 82

# ---- animation timing -----------------------------------------------------
BAR_DUR = 0.5
CARD_DELAY = 0.9


def chart_grid(data):
    """Return last-12-months entries: [(abbr, total), ...] most recent last."""
    months = data["monthly"][-12:]
    abbr = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    out = []
    for m in months:
        mm = m["month"][5:7]
        out.append((mm, m["total"]))
    # derive short English labels from YYYY-MM
    named = []
    for mm, total in out:
        label = datetime.date(2026, int(mm), 1).strftime("%b")
        named.append((label, total))
    return named


def build_svg(data):
    months = chart_grid(data)  # [(label, total), ...] chronological
    max_total = max((t for _, t in months), default=1) or 1

    stats = data
    total = stats["total_contributions"]
    cur = stats["current_streak"]["length"]
    longest = stats["longest_streak"]["length"]
    best = stats["best_day"]
    best_count = best["count"]
    active = stats["active_days"]
    year_days = len(stats["days"])
    activity_pct = round(active / year_days * 100) if year_days else 0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        "<style>",
        "@keyframes grow { 0%{transform:scaleY(0)} 100%{transform:scaleY(1)} }",
        "@keyframes fadeUp { 0%{opacity:0;transform:translateY(8px)} 100%{opacity:1;transform:translateY(0)} }",
        f".bar {{ transform-box:fill-box; transform-origin:bottom; animation:grow {BAR_DUR}s cubic-bezier(.2,.8,.2,1) both; }}",
        f".card {{ animation:fadeUp .5s cubic-bezier(.2,.8,.2,1) both; }}",
        f".fade {{ animation:fadeUp .4s ease-out both; }}",
        "@media (prefers-reduced-motion: reduce) { .bar,.card,.fade{animation:none!important;opacity:1!important;transform:none!important} }",
        "</style>",
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        f'<linearGradient id="barGrad" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="#0e4429"/><stop offset="1" stop-color="{GREEN}"/></linearGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" '
        f'stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
    ]

    # ---- titlebar ----
    parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>')
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
    parts.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">imzyrix@github: ~/activity --report</text>')
    ts = stats.get("generated_at", "")
    if ts:
        date_part = ts[:10]
    else:
        date_part = ""
    parts.append(f'<text x="{W - PAD}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="11" '
                 f'text-anchor="end">data {date_part}</text>')

    # ---- subtitle: headline stat ----
    parts.append(
        f'<text x="{PAD}" y="{TITLEBAR_H + SUBTITLE_H - 8}" font-size="14" fill="{TEXT}">'
        f'<tspan fill="{GREEN}" font-weight="700">{total}</tspan>'
        f'<tspan fill="{MUTED}"> contributions across last 12 months</tspan>'
        f'<tspan fill="{MUTED}">  &#183;  </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{active}</tspan>'
        f'<tspan fill="{MUTED}"> active days ({activity_pct}%)</tspan>'
        f'<tspan fill="{MUTED}">  &#183;  </tspan>'
        f'<tspan fill="{GOLD}" font-weight="700">{best_count}</tspan>'
        f'<tspan fill="{MUTED}"> best day</tspan></text>'
    )

    # ---- chart: y-axis gridlines + month labels + bars ----
    # y-axis
    parts.append(f'<text x="{PAD}" y="{CHART_TOP - 4}" font-size="10" fill="{MUTED}">{max_total}</text>')
    parts.append(f'<text x="{PAD}" y="{CHART_TOP + CHART_H + 3}" font-size="10" fill="{MUTED}">0</text>')
    parts.append(f'<line x1="{CHART_LEFT - 8}" y1="{CHART_TOP}" x2="{CHART_LEFT - 8}" y2="{CHART_TOP + CHART_H}" '
                 f'stroke="{FRAME}" stroke-opacity="0.35"/>')

    n = len(months)
    slot = CHART_W / n
    bar_w = min(34, slot * 0.55)
    for i, (label, val) in enumerate(months):
        cx = CHART_LEFT + i * slot + slot / 2
        h = (val / max_total) * CHART_H if max_total else 0
        bh = max(h, 3 if val > 0 else 0)
        # bar
        parts.append(
            f'<rect class="bar" x="{cx - bar_w / 2:.1f}" y="{CHART_TOP + CHART_H - bh:.1f}" '
            f'width="{bar_w:.1f}" height="{bh:.1f}" rx="3" fill="url(#barGrad)" '
            f'style="animation-delay:{0.1 + i * 0.05:.2f}s">'
            f'<title>{label}: {val} contributions</title></rect>'
        )
        # value label on top of bar (only when > 0)
        if val > 0:
            parts.append(
                f'<text x="{cx:.1f}" y="{CHART_TOP + CHART_H - bh - 6:.1f}" text-anchor="middle" '
                f'font-size="10" fill="{GREEN}" font-weight="700">{val}</text>'
            )
        # month label
        parts.append(
            f'<text x="{cx:.1f}" y="{CHART_TOP + CHART_H + 16}" text-anchor="middle" '
            f'font-size="10" fill="{MUTED}">{label}</text>'
        )

    # ---- stat cards ----
    cards = [
        ("TOTAL CONTRIBUTIONS", f"{total}", GREEN),
        ("CURRENT STREAK", f"{cur} days", ACCENT),
        ("LONGEST STREAK", f"{longest} days", GOLD),
        ("BEST DAY", f"{best_count}", RED),
    ]
    for i, (k, v, c) in enumerate(cards):
        x = PAD + i * (CARD_W + 12)
        y = CARDS_TOP
        parts.append(
            f'<g class="card" style="animation-delay:{CARD_DELAY + i * 0.1:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="10" fill="{BG2}" '
            f'stroke="{FRAME}" stroke-opacity="0.35"/>'
            f'<text x="{x + 14}" y="{y + 24}" font-size="10" fill="{MUTED}" '
            f'letter-spacing="1">{k}</text>'
            f'<text x="{x + 14}" y="{y + 60}" font-size="28" font-weight="700" fill="{c}">{v}</text>'
            f'</g>'
        )

    # ---- weekday activity ----
    parts.append(
        f'<text x="{PAD}" y="{WEEK_TOP}" font-size="11" fill="{MUTED}" letter-spacing="1">'
        f'WEEKDAY ACTIVITY</text>'
    )
    dow = weekday_totals(data)
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cmax = max(dow.values()) or 1
    for i, nm in enumerate(names):
        v = dow[i]
        x = PAD + i * ((W - PAD * 2) / 7)
        bh = (v / cmax) * 30 if v else 0
        parts.append(
            f'<g class="fade" style="animation-delay:{1.5 + i * 0.06:.2f}s">'
            f'<rect x="{x + 4}" y="{WEEK_TOP + 44 - bh:.1f}" width="18" height="{bh:.1f}" rx="2" '
            f'fill="{ACCENT}" opacity="0.7">'
            f'<title>{nm}: {v} contributions</title></rect>'
            f'<text x="{x + 13}" y="{WEEK_TOP + 64}" text-anchor="middle" font-size="9" '
            f'fill="{MUTED}">{nm}</text>'
            f'</g>'
        )

    # ---- footer ----
    parts.append(
        f'<line x1="0" y1="{FOOTER_TOP}" x2="{W}" y2="{FOOTER_TOP}" stroke="{FRAME}" stroke-opacity="0.25"/>'
    )
    parts.append(
        f'<text x="{PAD}" y="{FOOTER_TOP + 22}" font-size="12" fill="{MUTED}">'
        f'~$ ./activity.sh --since 12 months'
        f'<tspan fill="{INK}">  ready</tspan></text>'
    )
    # blinking cursor
    parts.append(
        f'<rect x="{PAD + 220}" y="{FOOTER_TOP + 12}" width="8" height="14" fill="{INK}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="1.1s" repeatCount="indefinite"/></rect>'
    )

    parts.append("</svg>")
    return "".join(parts)


def weekday_totals(data):
    """Return {weekday_index(Mon=0..Sun=6): total_contributions}."""
    totals = {i: 0 for i in range(7)}
    for day in data["days"]:
        dt = datetime.date.fromisoformat(day["date"])
        wd = dt.weekday()  # Mon=0 .. Sun=6
        totals[wd] += day["count"]
    return totals


def main():
    if not os.path.exists(IN_PATH):
        print(f"Run fetch_contributions.py first — missing {IN_PATH}")
        raise SystemExit(1)
    data = json.load(open(IN_PATH))
    svg = build_svg(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
