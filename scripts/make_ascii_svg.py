#!/usr/bin/env python3
"""Convert the prepped photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps each pixel's brightness
to a glyph from a density ramp, and wraps each row in a horizontal clip
that wipes left-to-right with a small block "cursor" riding the edge.
Staggered top to bottom; prints once and freezes (no looping).

Usage:
    python scripts/make_ascii_svg.py   # reads data/source-prepped.png
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "avi-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)

WIDTH = 100              # target character columns
COLS = 52 * 2            # total grid columns (tileable)
CHARS_W = 100            # rendered character width in svg units
CHARS_H = 180            # rendered character height in svg units
FONT = "monospace"
FILL = "#c9d1d9"         # light-gray monochrome on dark background

# Per-row wipe duration and stagger (seconds).
ROW_TIME = 0.14
ROW_STAGGER = 0.05


def sample_grid(img: Image.Image) -> list[list[str]]:
    """Return a 2D grid of ramp glyphs for a character grid of COLS wide."""
    w, h = img.size
    target_h = max(8, round(h / w * COLS))
    small = img.resize((COLS, target_h), Image.LANCZOS).convert("L")

    grid = []
    for y in range(target_h):
        row = []
        for x in range(COLS):
            p = small.getpixel((x, y))
            idx = int(p / 255 * (len(RAMP) - 1))
            row.append(RAMP[idx])
        grid.append(row)
    return grid


def build_svg(grid: list[list[str]]) -> str:
    rows = len(grid)
    cols = len(grid[0])
    # Use a monospace char cell aspect from the em-box (approx 0.55 wide/high).
    cw = CHARS_W
    ch = CHARS_H
    width = cols * cw
    height = rows * ch

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="{FONT}" font-size="{ch}">'
    )

    for r, row in enumerate(grid):
        y = r * ch
        start = r * ROW_STAGGER

        # Vertical reveal envelope (row prints only after previous rows start).
        parts.append(
            f'  <clipPath id="row{r}"><rect x="0" y="{y}" '
            f'width="{width}" height="{ch}"/></clipPath>'
        )

        # Cursor: small block that rides the wipe edge.
        segments = []
        for i, glyph in enumerate(row):
            x = i * cw
            cx = x + ROW_TIME * 1000 * cw / 1000  # not used; cursor below
            segments.append(
                f'<text x="{x}" y="{y + ch * 0.8}">{glyph}</text>'
            )
        text = "\n".join(segments)

        anim = (
            f'<animate attributeName="x" from="{width}" to="0" '
            f'begin="{start}s" dur="{ROW_TIME}s" fill="freeze" '
            f'id="anim{r}"/>'
        )
        # Horizontal wipe: translate the text group from right to left.
        parts.append(
            f'  <g clip-path="url(#row{r})">'
            f'<g>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{width} 0" to="0 0" begin="{start}s" dur="{ROW_TIME}s" '
            f'fill="freeze"/>'
            f'<g fill="{FILL}" stroke="none">{text}</g>'
            f'<rect x="-6" y="{y}" width="6" height="{ch}" fill="{FILL}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{width} 0" to="0 0" begin="{start}s" dur="{ROW_TIME}s" '
            f'fill="freeze"/></rect>'
            f'</g></g>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    src = DATA / "source-prepped.png"
    if not src.exists():
        print(f"Run prep_photo.py first — missing {src}")
        return
    img = Image.open(src)
    grid = sample_grid(img)
    OUT.write_text(build_svg(grid))
    print(f"Wrote {OUT} ({len(grid[0])}x{len(grid)} chars)")


if __name__ == "__main__":
    main()
