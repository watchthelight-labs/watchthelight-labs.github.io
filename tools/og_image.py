#!/usr/bin/env python3
# <wtl> project: watchthelight-labs.github.io | file: tools/og_image.py | author: watchthelight </wtl>
"""Link-preview images (1200x630): the starfield, the sage mark and a name. Nothing else.

  python tools/og_image.py site OUT.png                 # "watchthelight labs"
  python tools/og_image.py repo OUT.png NAME            # the repo name, with "watchthelight labs" small above it

Fonts: tools/fonts/SpaceMono-Bold.ttf and -Regular.ttf (SIL OFL, see tools/fonts/OFL.txt). Deterministic per
name, so a rebuild gives the same image.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent / "fonts"
W, H = 1200, 630
BG, TEXT, DIM, SAGE, FAINT = (8, 8, 12), (225, 229, 232), (110, 114, 122), (106, 154, 110), (42, 45, 51)


def stars(d, seed, keep_clear):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = keep_clear
    for _ in range(380):
        x, y = rnd.randrange(W), rnd.randrange(H)
        if x0 < x < x1 and y0 < y < y1:
            continue
        a = rnd.uniform(0.15, 0.7)
        s = 2 if rnd.random() < 0.18 else 1
        col = SAGE if rnd.random() < 0.08 else (200, 210, 220)
        d.rectangle([x, y, x + s - 1, y + s - 1], fill=tuple(int(BG[i] + (col[i] - BG[i]) * a) for i in range(3)))


def fit(text, size, max_w):
    """Largest Space Mono Bold size (down from `size`) at which `text` fits in max_w pixels."""
    while size > 28:
        f = ImageFont.truetype(str(FONTS / "SpaceMono-Bold.ttf"), size)
        if f.getlength(text) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(FONTS / "SpaceMono-Bold.ttf"), size)


def draw(out: Path, title: str, kicker: str = ""):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    left, max_w = 96, W - 96 * 2 - 44
    big = fit(title, 76, max_w)
    tw = big.getlength(title)
    cy = H // 2
    stars(d, title, (left - 30, cy - 120, left + 44 + tw + 30, cy + 90))
    asc, desc = big.getmetrics()
    ty = cy - (asc + desc) // 2
    d.rectangle([left, cy - 4, left + 21, cy + 17], fill=SAGE)                  # the mark, level with the x-height
    d.text((left + 44, ty), title, font=big, fill=TEXT)
    if kicker:
        small = ImageFont.truetype(str(FONTS / "SpaceMono-Regular.ttf"), 24)
        d.text((left + 44, ty - 34), kicker, font=small, fill=DIM)
    d.rectangle([0, H - 4, W, H], fill=FAINT)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)


def main():
    mode, out = sys.argv[1], Path(sys.argv[2])
    if mode == "site":
        draw(out, "watchthelight labs")
    else:
        draw(out, sys.argv[3], "watchthelight labs")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
