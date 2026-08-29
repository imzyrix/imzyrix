#!/usr/bin/env python3
"""Prep a photo for ASCII conversion.

Removes the background (rembg), boosts local contrast (OpenCV CLAHE),
and composites onto pure white so the background maps to the blank end
of the ASCII ramp. Outputs data/source-prepped.png. Run once per photo.

Usage:
    python scripts/prep_photo.py source-photo.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"Photo not found: {src}")
        sys.exit(1)

    # 1. Remove background so the subject is isolated.
    img = Image.open(src).convert("RGBA")
    cut = remove(img).convert("RGBA")

    # 2. Extract the subject onto white, then boost local contrast.
    rgba = np.array(cut)
    alpha = rgba[..., 3:4] / 255.0
    white = np.full_like(rgba[..., :3], 255)
    subject = (rgba[..., :3] * alpha + white * (1.0 - alpha)).astype(np.uint8)

    gray = cv2.cvtColor(subject, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 3. Auto-crop to the non-white bounding box, then square-pad to a
    #    square so portrait aspect is preserved through downsampling.
    mask = gray < 245
    ys, xs = np.where(mask)
    if len(xs) == 0:
        print("No subject found in image.")
        sys.exit(1)
    x1, x2, y1, y2 = xs.min(), xs.max(), ys.min(), ys.max()
    gray = gray[y1 : y2 + 1, x1 : x2 + 1]

    h, w = gray.shape
    side = max(h, w)
    canvas = np.full((side, side), 255, dtype=np.uint8)
    top = (side - h) // 2
    left = (side - w) // 2
    canvas[top : top + h, left : left + w] = gray

    out = DATA / "source-prepped.png"
    Image.fromarray(canvas).save(out)
    print(f"Wrote {out} ({side}x{side})")


if __name__ == "__main__":
    main()
