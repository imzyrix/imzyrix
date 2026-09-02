"""
Render data/discord.json as an enhanced dark-terminal Discord presence card.

Self-contained SVG (no JS); the avatar and avatar-decoration are embedded as
base64 data URIs so the file renders on GitHub with no external fetches.

Shown:
  - terminal titlebar
  - real avatar in a circle, with the avatar-decoration frame on top
  - HypeSquad / other discord badge chips decoded from public_flags
  - status pill (Online / Idle / Do Not Disturb / Offline)
  - display name + username
  - current activity (custom status / game / Spotify)
  - social links row (website / instagram / youtube / reddit / orgs)

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
INK = "#c9d1d8"
SOCIAL = "#8b949e"

STATUS = {
    "online": ("#23a559", "Online"),
    "idle": ("#f0b232", "Idle"),
    "dnd": ("#f23f43", "Do Not Disturb"),
    "offline": ("#80848e", "Offline"),
}

# discord public_flags -> badge (name, brand color)
def decode_flags(flags):
    badges = []
    tab = {
        1 << 0: ("Staff", "#5865f2"),
        1 << 1: ("Partner", "#f0b232"),
        1 << 2: ("HypeSquad Events", "#f0b232"),
        1 << 3: ("Bug Hunter", "#f23f43"),
        1 << 6: ("Bravery", "#f47b67"),
        1 << 7: ("Brilliance", "#f47b67"),
        1 << 8: ("Balance", "#f23f43"),
        1 << 9: ("Early Supporter", "#f0b232"),
        1 << 14: ("Bug Hunter L2", "#f23f43"),
        1 << 17: ("Early Dev", "#23a559"),
        1 << 18: ("Moderator", "#23a559"),
        1 << 22: ("Active Dev", "#23a559"),
    }
    for bit, (name, color) in tab.items():
        if flags & bit:
            badges.append((name, color))
    return badges

W = 860
H = 250
TITLEBAR_H = 30
PAD = 16
AVATAR = 86
AX = PAD
AY = TITLEBAR_H + 34


def build_svg(data):
    cfg = data.get("configured", False)
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        "<style>",
        "@keyframes pop {0%{opacity:0;transform:scale(.8)}60%{opacity:1;transform:scale(1.06)}100%{opacity:1;transform:scale(1)}}",
        "@keyframes fade {from{opacity:0}to{opacity:1}}",
        f".a{{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .5s ease-out .05s both;}}",
        f".b{{animation:fade .5s ease-out .3s both;}}",
        "@media (prefers-reduced-motion: reduce){.a,.b{animation:none!important;opacity:1!important;transform:none!important}}",
        "</style>",
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        f'<clipPath id="aclip"><circle cx="{AX + AVATAR / 2}" cy="{AY + AVATAR / 2}" r="{AVATAR / 2 - 2}"/></clipPath>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" '
        f'stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
    p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">imzyrix@github: ~ Discord / presence --live</text>')

    if not cfg or data.get("error"):
        p.append(f'<text x="{PAD}" y="{AY + 20}" fill="{MUTED}" font-size="14" class="b">'
                 f'Discord presence is unconfigured / unavailable.</text>')
        p.append(f'<text x="{PAD}" y="{AY + 44}" fill="{MUTED}" font-size="12" class="b">'
                 f'set DISCORD_USER_ID secret + join the Lanyard server to enable.</text>')
    else:
        status = data.get("status", "offline")
        color, stat_name = STATUS.get(status, ("#80848e", status.title()))
        uname = data.get("display_name") or data.get("username")
        username = data.get("username", "")
        badges = decode_flags(data.get("public_flags", 0))
        av_b64 = data.get("avatar_b64", "")
        dec_b64 = data.get("decoration_b64", "")

        # ---- avatar + decoration ----
        cxm, cym = AX + AVATAR / 2, AY + AVATAR / 2
        # decoration frame behind/around the avatar
        if dec_b64:
            p.append(
                f'<g class="a">'
                f'<image href="data:image/png;base64,{dec_b64}" x="{AX - 14}" y="{AY - 14}" '
                f'width="{AVATAR + 28}" height="{AVATAR + 28}" preserveAspectRatio="xMidYMid meet"/>'
                f'</g>'
            )
        # status ring
        p.append(
            f'<circle cx="{cxm}" cy="{cym}" r="{AVATAR / 2 + 5}" fill="none" '
            f'stroke="{color}" stroke-width="3" opacity="0.9" class="b"/>'
        )
        # avatar image clipped to circle
        if av_b64:
            p.append(
                f'<g clip-path="url(#aclip)" class="a">'
                f'<image href="data:image/png;base64,{av_b64}" x="{AX}" y="{AY}" '
                f'width="{AVATAR}" height="{AVATAR}" preserveAspectRatio="xMidYMid slice"/>'
                f'</g>'
            )
        else:
            p.append(f'<circle cx="{cxm}" cy="{cym}" r="{AVATAR / 2}" fill="{BG2}" class="a"/>')
            p.append(f'<text x="{cxm}" y="{cym + 6}" font-size="30" font-weight="700" fill="{TEXT}" '
                     f'text-anchor="middle" class="a">{uname[0].upper()}</text>')

        # ---- name / username / status ----
        tx = AX + AVATAR + 26
        namey = AY + 26
        p.append(f'<text x="{tx}" y="{namey}" font-size="20" font-weight="700" fill="{TEXT}" class="b">'
                 f'{uname}</text>')
        # badge chips next to name
        bx = tx + len(uname) * 12.5 + 12
        for i, (bname, bcolor) in enumerate(badges[:4]):
            p.append(
                f'<g class="a">'
                f'<rect x="{bx + i * 26}" y="{namey - 15}" width="20" height="20" rx="5" '
                f'fill="{bcolor}">'
                f'<title>{bname}</title></rect>'
                f'<text x="{bx + i * 26 + 10}" y="{namey}" font-size="10" font-weight="800" '
                f'fill="#fff" text-anchor="middle">{"H" if "Brilliance" in bname else "*"}</text>'
                f'</g>'
            )
        # status pill
        sw = 24 + len(stat_name) * 7.4 if stat_name else 24
        pw = W - PAD - sw
        p.append(
            f'<g class="a">'
            f'<rect x="{pw}" y="{AY - 2}" width="{sw:.0f}" height="24" rx="12" fill="{BG2}" '
            f'stroke="{color}" stroke-opacity="0.8"/>'
            f'<circle cx="{pw + 15}" cy="{AY + 10}" r="4.5" fill="{color}"/>'
            f'<text x="{pw + 27}" y="{AY + 14}" font-size="12" fill="{color}" '
            f'font-weight="700">{stat_name}</text>'
            f'</g>'
        )
        # username + desktop/mobile indicator
        p.append(
            f'<text x="{tx}" y="{namey + 22}" font-size="13" fill="{INK}" class="b">'
            f'@{username}</text>'
        )
        # activity line
        act = activity_line(data)
        if act:
            p.append(
                f'<text x="{tx}" y="{namey + 46}" font-size="13" fill="{INK}" class="b">'
                f'<tspan fill="{STATUS[status][0]}" font-weight="700">&#9654;</tspan> '
                f'{act}</text>'
            )
        else:
            p.append(
                f'<text x="{tx}" y="{namey + 46}" font-size="13" fill="{MUTED}" class="b">'
                f'<tspan fill="{color}" font-weight="700">&#9654;</tspan> no active activity</text>'
            )

        # ---- social links row ----
        links = [
            ("zyrix.qzz.io", "https://zyrix.qzz.io", "web"),
            ("@imzyrix", "https://www.instagram.com/imzyrix/", "ig"),
            ("@zyrix-dev", "https://www.youtube.com/@zyrix-dev", "yt"),
            ("u/imzyrix", "https://www.reddit.com/user/imzyrix/", "rd"),
            ("ZyrixDevelopment", "https://github.com/ZyrixDevelopment", "gh"),
            ("aequiarch-org", "https://github.com/aequiarch-org", "gh"),
        ]
        ly = H - 26
        p.append(f'<line x1="0" y1="{H - 44}" x2="{W}" y2="{H - 44}" stroke="{FRAME}" stroke-opacity="0.25"/>')
        p.append(f'<text x="{PAD}" y="{ly}" font-size="10" fill="{MUTED}" letter-spacing="1" class="b">'
                 f'LINKS</text>')
        lx = PAD + 48
        for label, url, kind in links:
            marker = {"ig": "IG", "yt": "YT", "rd": "R/", "gh": "GH"}.get(kind, "WWW")
            seg_len = len(f'[{marker}] {label}')
            p.append(f'<a href="{url}" target="_blank">'
                     f'<text x="{lx}" y="{ly}" font-size="11" fill="{SOCIAL}" class="b">'
                     f'<tspan fill="{ACCENT}" font-weight="700">[{marker}]</tspan> {label}</text>'
                     f'</a>')
            lx += seg_len * 7.4 + 22

    p.append("</svg>")
    return "".join(p)


ACCENT = "#58a6ff"


def activity_line(data):
    activities = data.get("activities") or []
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


def main():
    if not os.path.exists(IN_PATH):
        print(f"Run fetch_discord.py first — missing {IN_PATH}")
        raise SystemExit(1)
    data = json.load(open(IN_PATH))
    svg = build_svg(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)//1024}KB)")


if __name__ == "__main__":
    main()
