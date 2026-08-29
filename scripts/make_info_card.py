#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG.

A title bar, then colored key/value rows — Now, Prev, Stack, Highlights.
Each line fades and slides in on a short stagger so the panel looks like
it's printing next to the portrait.

Set STATIC=1 to emit a frozen frame for local Quick Look previews.

Usage:
    python scripts/make_info_card.py   # writes info-card.svg
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

W, H = 620, 460
BG = "#0d1117"
FG = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#58a6ff"
CELL = "#161b22"
BORDER = "#30363d"

STATIC = os.environ.get("STATIC") == "1"


def rows() -> list[tuple[str, str, str]]:
    """Return (label, value, color) per neofetch line."""
    return [
        ("imzyrix@github", "OS", ACCENT),
        ("", "", FG),  # divider
        ("Now", "building tools & visual experiments", FG),
        ("Prev", "systems, web & game dev", FG),
        ("Stack", "Python · JS/TS · Three.js · WebGL", FG),
        ("Shell", "zsh + tmux, always", DIM),
        ("Card", "neofetch-style, 100% SVG", DIM),
        ("", "", FG),
        ("Highlights", "self-typing ASCII portrait", FG),
        ("", "live contribution heatmap", FG),
        ("", "no JS, no tokens, all committed", FG),
    ]


def row_svg(i: int, label: str, value: str, color: str, y: int) -> str:
    stagger = 0.12 * i
    if STATIC:
        fade = f'opacity="1"'
        slide = ""
    else:
        # Print-like fade + slide, staggered per line, freeze.
        fade = (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{stagger}s" dur="0.6s" fill="freeze"/>'
        )
        slide = (
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 8" to="0 0" begin="{stagger}s" dur="0.6s" '
            f'fill="freeze"/>'
        )
    if not label:
        # Divider row: a hairline.
        return (
            f'<g><rect x="26" y="{y + 6}" width="{W - 52}" height="1" '
            f'fill="{BORDER}"/>{fade}</g>'
        )
    label_x = 34
    value_x = 150
    return (
        f'<g>{slide}<text x="{label_x}" y="{y}" '
        f'font-family="monospace" font-size="17" fill="{ACCENT}">'
        f'{label}</text>'
        f'<text x="{value_x}" y="{y}" font-family="monospace" '
        f'font-size="17" fill="{color}">{value}</text>'
        f'{fade}</g>'
    )


def build_svg() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
        f'height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="12"/>',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{CELL}" '
        f'rx="12" stroke="{BORDER}" stroke-width="1"/>',
        # Title bar.
        '<rect x="0" y="0" width="620" height="44" fill="#161b22" rx="12"/>'
        '<rect x="0" y="22" width="620" height="22" fill="#161b22"/>'
        '<text x="22" y="29" font-family="monospace" font-size="15" '
        f'fill="{DIM}">imzyrix@github — ~/profile</text>',
    ]
    y = 84
    i = 0
    for label, value, color in rows():
        parts.append(row_svg(i, label, value, color, y))
        if not label and not value:
            y += 26
        else:
            y += 34
        i += 1
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    OUT.write_text(build_svg())
    print(f"Wrote {OUT}" + (" (STATIC)" if STATIC else ""))


if __name__ == "__main__":
    main()
