"""
Prepare an avatar/photo with a SOLID background for clean ASCII conversion,
without needing rembg (no big model download).

Use this when the source image has a uniform background color (e.g. a GitHub
profile picture). It:
  1. segments the subject by color-distance from the corner background color
  2. boosts LOCAL contrast (CLAHE) on the subject
  3. composites the subject onto pure white so the background maps to blank

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

For a photo with a real (non-solid) background, use the rembg-based
prep_photo.py instead.

    python scripts/prep_solid_bg.py <input.jpg> [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

# how far (0..255) a pixel may be from the corner color and still count as
# background. The subject is assumed to occupy the middle of the frame.
BG_DIST = 40
SAMPLE_INSET = 8          # sample the corner from this many px in
FEATHER = 1.0             # gaussian sigma on the alpha mask (avoid a halo)


def main():
    img = Image.open(INP).convert("RGB")
    rgb = np.array(img).astype(np.float32)
    h, w, _ = rgb.shape

    # background color = average of the four corners
    corners = np.concatenate([
        rgb[SAMPLE_INSET:SAMPLE_INSET+1, SAMPLE_INSET:SAMPLE_INSET+1],
        rgb[SAMPLE_INSET:SAMPLE_INSET+1, w-SAMPLE_INSET-1:w-SAMPLE_INSET],
        rgb[h-SAMPLE_INSET-1:h-SAMPLE_INSET, SAMPLE_INSET:SAMPLE_INSET+1],
        rgb[h-SAMPLE_INSET-1:h-SAMPLE_INSET, w-SAMPLE_INSET-1:w-SAMPLE_INSET],
    ], axis=0).reshape(4, 3).mean(axis=0)

    dist = np.sqrt(((rgb - corners) ** 2).sum(axis=2))
    alpha = (dist > BG_DIST).astype(np.float32)   # 1 = subject
    alpha = cv2.GaussianBlur(alpha, (0, 0), FEATHER)

    # 2. local-contrast the luminance (CLAHE) on the subject only
    gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)

    # 3. composite onto white using the subject alpha
    if alpha.max() <= 0:
        print("no subject detected (background not solid?) -- try prep_photo.py (rembg)")
        sys.exit(1)
    out = gray.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)
    out = np.clip(out, 0, 255).astype(np.uint8)

    Image.fromarray(out, mode="L").save(OUT)
    print("wrote", OUT, out.shape, "bg color", corners.astype(int))


if __name__ == "__main__":
    main()
