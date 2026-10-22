#!/usr/bin/env python3
# <wtl> project: watchthelight-labs.github.io | file: tools/og_image.py | author: watchthelight </wtl>
"""Draw src/og.png (1200x630), the link preview Discord and others show: the starfield, the mark, the name, the
tagline, the address. Deterministic, so rebuilding it gives the same image.

  python tools/og_image.py --font-bold SpaceMono-Bold.ttf --font SpaceMono-Regular.ttf
"""
import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1200, 630
BG, TEXT, DIM, SAGE, FAINT = (8, 8, 12), (225, 229, 232), (138, 142, 150), (106, 154, 110), (42, 45, 51)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font-bold", required=True)
    ap.add_argument("--font", required=True)
    a = ap.parse_args()
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    rnd = random.Random(1401)
    # square-pixel stars, denser at the top right, kept clear of the text block
    for _ in range(420):
        x, y = rnd.randrange(W), rnd.randrange(H)
        if 70 < x < 860 and 180 < y < 500:
            continue
        a_ = rnd.uniform(0.15, 0.7)
        s = 2 if rnd.random() < 0.18 else 1
        col = SAGE if rnd.random() < 0.08 else (200, 210, 220)
        c = tuple(int(BG[i] + (col[i] - BG[i]) * a_) for i in range(3))
        d.rectangle([x, y, x + s - 1, y + s - 1], fill=c)
    # one shooting star
    for i in range(110):
        t = i / 110
        x, y = int(860 + i * 2.2), int(70 + i * 0.9)
        c = tuple(int(BG[k] + (200 - BG[k]) * t * 0.75) for k in range(3))
        d.point((x, y), fill=c)
    bold = ImageFont.truetype(a.font_bold, 68)
    reg = ImageFont.truetype(a.font, 27)
    small = ImageFont.truetype(a.font, 22)
    left, top = 90, 210
    d.rectangle([left, top + 47, left + 21, top + 68], fill=SAGE)               # the mark
    d.text((left + 44, top - 4), "watchthelight labs", font=bold, fill=TEXT)
    d.rectangle([left, top + 104, left + 120, top + 105], fill=SAGE)            # thin sage rule
    d.text((left, top + 128), "macOS drivers and tools for hardware", font=reg, fill=DIM)
    d.text((left, top + 166), "Apple never shipped drivers for.", font=reg, fill=SAGE)
    d.text((left, H - 78), "labs.watchthelight.org", font=small, fill=DIM)
    d.rectangle([0, H - 4, W, H], fill=FAINT)
    out = ROOT / "src" / "og.png"
    img.save(out, optimize=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
