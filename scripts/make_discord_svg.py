"""
Render data/discord.json as a dark-terminal Discord presence card.

Self-contained SVG (no JS), reveals once on load then freezes so GitHub's
sandboxed rendering plays it. Components:

  - terminal titlebar (traffic lights + live Discord presence)
  - status pill (Online / Idle / Do Not Disturb / Offline) with a colored dot
  - Discord display name + avatar
  - current activity line (custom status / game / Spotify track + progress)
  - footer with a steady blinking cursor

Usage:
    python scripts/make_discord_svg.py     # writes discord-presence.svg
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "discord.json")
OUT_PATH = os.path.join(HERE, "..", "discord-presence.svg")

# ---- palette ---------------------------------------------------------------
BG = "#0a0e14"
BG2 = "#0d1420"
FRAME = "#5865f2"            # Discord blurple
MUTED = "#9aa3b2"
TEXT = "#e6edf3"
INK = "#c9d1d9"

STATUS = {
    "online": ("#23a559", "Online"),
    "idle": ("#f0b232", "Idle"),
    "dnd": ("#f23f43", "Do Not Disturb"),
    "offline": ("#80848e", "Offline"),
}

W = 860
H = 150
TITLEBAR_H = 30
PAD = 16


def anim_css(dur, delay, transform):
    return (f"transform-box:fill-box;transform-origin:center;opacity:0;"
            f"animation:pop {dur}s ease-out {delay}s both;")


def status_line(data):
    """Return a human line about current activity, or None."""
    activities = data.get("activities") or []
    # prioritize: spotify > custom status > first rich/game activity
    art = [a for a in activities if a.get("type") == 0]
    custom = [a for a in activities if a.get("type") == 4]
    if data.get("listening_to_spotify") and data.get("spotify"):
        s = data["spotify"]
        return f'Listening to {s.get("song")} — {s.get("artist")}'
    if custom:
        return custom[0].get("state") or "Custom status"
    for a in art:
        name = a.get("name")
        state = a.get("state") or a.get("details")
        if state:
            return f"{name}: {state}"
        if name:
            return f"Playing {name}"
    return None


def build_svg(data):
    cfg = data.get("configured", False)

    # header/titlebar text
    title = "~ Discord / presence --live"
    if not cfg:
        veracity = "unconfigured"
    else:
        veracity = data.get("user_id", "?")
    if data.get("error"):
        veracity = "unavailable"

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        "<style>",
        "@keyframes pop {0%{opacity:0;transform:scale(.8)}60%{opacity:1;transform:scale(1.06)}100%{opacity:1;transform:scale(1)}}",
        "@keyframes fade {from{opacity:0}to{opacity:1}}",
        f".a {{ {anim_css('.5s', '.05s', '')} }}",
        "@media (prefers-reduced-motion: reduce){.a{animation:none!important;opacity:1!important;transform:none!important}}",
        "</style>",
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" '
        f'stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
    p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">imzyrix@github: {title}</text>')

    content_top = TITLEBAR_H + (H - TITLEBAR_H) / 2

    if not cfg or data.get("error"):
        # placeholder card
        p.append(
            f'<text x="{PAD}" y="{content_top}" fill="{MUTED}" font-size="14" class="a">'
            f'Discord presence is unconfigured for {veracity}.</text>'
        )
        p.append(
            f'<text x="{W - PAD}" y="{H - PAD - 8}" fill="{MUTED}" font-size="11" '
            f'text-anchor="end">set DISCORD_USER_ID + join the Lanyard server to enable</text>'
        )
    else:
        status = data.get("status", "offline")
        color, stat_name = STATUS.get(status, ("#80848e", status.title()))
        uname = data.get("display_name") or data.get("username")
        act = status_line(data)

        # status pill (top-right)
        pw = 24 + len(stat_name) * 7.2
        px = W - PAD - pw
        p.append(
            f'<g class="a">'
            f'<rect x="{px}" y="{TITLEBAR_H + 16}" width="{pw:.0f}" height="24" rx="12" '
            f'fill="{BG2}" stroke="{color}" stroke-opacity="0.8"/>'
            f'<circle cx="{px + 16}" cy="{TITLEBAR_H + 28}" r="4.5" fill="{color}"/>'
            f'<text x="{px + 28}" y="{TITLEBAR_H + 32}" font-size="12" fill="{TEXT}" '
            f'font-weight="700">{stat_name}</text>'
            f'</g>'
        )

        # avatar (rounded square placeholder — Discord avatar, no external fetch
        # in the SVG body; we show a monogram tile instead)
        ay = TITLEBAR_H + 24
        aname = (uname or "Z")[0].upper()
        p.append(
            f'<g class="a">'
            f'<rect x="{PAD}" y="{ay - 18}" width="60" height="60" rx="14" fill="{FRAME}"/>'
            f'<text x="{PAD + 30}" y="{ay + 16}" font-size="30" font-weight="700" '
            f'fill="#ffffff" text-anchor="middle">{aname}</text>'
            f'</g>'
        )

        # display name
        p.append(
            f'<g class="a">'
            f'<text x="{PAD + 76}" y="{ay - 2}" font-size="17" font-weight="700" '
            f'fill="{TEXT}">{uname}</text>'
            f'</g>'
        )
        # activity line
        if act:
            p.append(
                f'<g class="a">'
                f'<text x="{PAD + 76}" y="{ay + 20}" font-size="13" fill="{INK}">{act}</text>'
                f'</g>'
            )
            # small "now playing" bar
            p.append(
                f'<rect x="{PAD + 76}" y="{ay + 30}" width="220" height="4" rx="2" fill="{BG2}" '
                f'opacity="0.5"/>'
            )
        else:
            p.append(
                f'<text x="{PAD + 76}" y="{ay + 20}" font-size="13" fill="{MUTED}">'
                f'no active activity</text>'
            )

        # footer
        p.append(
            f'<text x="{PAD}" y="{H - 12}" font-size="11" fill="{MUTED}">'
            f'@ {data.get("username")} </text>'
            f'<text x="{W - PAD}" y="{H - 12}" font-size="11" fill="{MUTED}" text-anchor="end">'
            f'updated daily</text>'
        )

    p.append("</svg>")
    return "".join(p)


def main():
    if not os.path.exists(IN_PATH):
        print(f"Run fetch_discord.py first — missing {IN_PATH}")
        raise SystemExit(1)
    data = json.load(open(IN_PATH))
    svg = build_svg(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
