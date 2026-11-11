#!/usr/bin/env python3
"""Circle the changed part of a proof screenshot and write a caption under it.

Usage:
  python3 -I annotate.py <in.png> <out.png> --box X,Y,W,H --caption "text" [--color red]

--box is the region in pixels (left, top, width, height) that shows the bug or the fix.
Run it on the before image and the after image of the same step, with the same box
when the same area changed. Keep the original untouched and write to annotated/.
"""
import argparse
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--box", required=True, help="X,Y,W,H in pixels")
    ap.add_argument("--caption", required=True)
    ap.add_argument("--color", default="red")
    a = ap.parse_args()

    x, y, w, h = (int(v) for v in a.box.split(","))
    img = Image.open(a.src).convert("RGB")
    if x < 0 or y < 0 or x + w > img.width or y + h > img.height or w < 10 or h < 10:
        raise SystemExit(f"box {a.box} is outside the {img.width}x{img.height} image")

    draw = ImageDraw.Draw(img)
    pad = 8
    draw.rounded_rectangle((x - pad, y - pad, x + w + pad, y + h + pad), radius=18, outline=a.color, width=5)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except OSError:
        font = ImageFont.load_default()
    lines = textwrap.wrap(a.caption, width=max(30, img.width // 15))
    line_h = 34
    bar = line_h * len(lines) + 24
    out = Image.new("RGB", (img.width, img.height + bar), "white")
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    for i, line in enumerate(lines):
        d.text((16, img.height + 12 + i * line_h), line, fill="black", font=font)

    Path(a.dst).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.dst)
    print(f"wrote {a.dst} ({out.width}x{out.height})")


if __name__ == "__main__":
    main()
