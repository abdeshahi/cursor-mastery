#!/usr/bin/env python3
"""Sanity-check 390px-wide cover crops for owner-approved homepage assets."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "assets" / "owner-approved"
MOBILE_W = 390

FOCAL = {
    "futuristic_blue_tech_showcase.webp": (0.26, 0.42),
    "futuristic_blue_smartphone_showcase.webp": (0.24, 0.42),
    "futuristic_tech_accessories_still_life.webp": (0.76, 0.46),
    "futuristic_purple_earbuds_studio_render.webp": (0.22, 0.40),
    "futuristic_teal_smartwatch_hero_scene.webp": (0.24, 0.38),
    "certified_smartphone_golden_halo.webp": (0.24, 0.42),
    "futuristic_contactless_payment_showcase.webp": (0.72, 0.38),
}


def cover_crop_box(w: int, h: int, view_w: int, view_h: int, fx: float, fy: float) -> tuple[int, int, int, int]:
    scale = max(view_w / w, view_h / h)
    cw, ch = int(w * scale), int(h * scale)
    cx = int((cw - view_w) * fx)
    cy = int((ch - view_h) * fy)
    cx = max(0, min(cx, cw - view_w))
    cy = max(0, min(cy, ch - view_h))
    x0 = int(cx / scale)
    y0 = int(cy / scale)
    x1 = int((cx + view_w) / scale)
    y1 = int((cy + view_h) / scale)
    return x0, y0, min(w, x1), min(h, y1)


def main() -> None:
    ok = True
    for name, (fx, fy) in FOCAL.items():
        path = ROOT / name
        if not path.is_file():
            print(f"MISSING {name}")
            ok = False
            continue
        im = Image.open(path)
        w, h = im.size
        view_h = 260 if "tech_showcase" in name else 140 if "golden_halo" in name and False else 128
        if "tech_showcase" in name and "blue_tech" in name:
            view_h = 260
        elif name == "certified_smartphone_golden_halo.webp":
            view_h = 140
        else:
            view_h = 128
        box = cover_crop_box(w, h, MOBILE_W, view_h, fx, fy)
        crop = im.crop(box)
        # Ensure non-empty crop and reasonable luminance (not a flat edge)
        extrema = crop.convert("L").getextrema()
        if extrema[1] - extrema[0] < 8:
            print(f"LOW CONTRAST crop {name} {box}")
            ok = False
        else:
            print(f"OK {name} crop={box} range={extrema}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
