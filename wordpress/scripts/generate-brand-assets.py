#!/usr/bin/env python3
"""Generate CTTEL brand placeholder PNGs (minimal, no text)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent / "assets" / "brand"
PRIMARY = (40, 114, 250)  # #2872fa
BG = (248, 250, 252)  # #f8fafc
BG2 = (239, 246, 255)  # #eff6ff
WHITE = (255, 255, 255)


def lerp_bg() -> Image.Image:
    img = Image.new("RGB", (1200, 900), BG)
    draw = ImageDraw.Draw(img)
    for y in range(900):
        t = y / 900
        r = int(BG[0] * (1 - t) + BG2[0] * t)
        g = int(BG[1] * (1 - t) + BG2[1] * t)
        b = int(BG[2] * (1 - t) + BG2[2] * t)
        draw.line([(0, y), (1200, y)], fill=(r, g, b))
    return img


def draw_hero() -> Image.Image:
    img = lerp_bg()
    draw = ImageDraw.Draw(img)
    # Phone silhouette
    cx, cy = 600, 430
    draw.rounded_rectangle((cx - 95, cy - 170, cx + 95, cy + 170), radius=36, fill=WHITE, outline=PRIMARY, width=4)
    draw.rounded_rectangle((cx - 78, cy - 130, cx + 78, cy + 120), radius=12, fill=BG2)
    draw.ellipse((cx - 18, cy + 135, cx + 18, cy + 155), fill=PRIMARY)
    # Small gadget accent
    draw.rounded_rectangle((cx + 180, cy - 40, cx + 280, cy + 60), radius=20, fill=WHITE, outline=PRIMARY, width=3)
    draw.ellipse((cx + 205, cy - 15, cx + 255, cy + 35), outline=PRIMARY, width=3)
    return img


def tile_base() -> Image.Image:
    img = Image.new("RGB", (512, 512), WHITE)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((16, 16, 496, 496), radius=32, fill=BG, outline=(226, 232, 240), width=2)
    return img, draw


def icon_mobile(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 256
    draw.rounded_rectangle((cx - 70, cy - 120, cx + 70, cy + 120), radius=24, fill=WHITE, outline=PRIMARY, width=5)
    draw.rounded_rectangle((cx - 54, cy - 88, cx + 54, cy + 88), radius=10, fill=BG2)
    draw.ellipse((cx - 12, cy + 95, cx + 12, cy + 108), fill=PRIMARY)


def icon_headphones(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 270
    draw.arc((cx - 100, cy - 120, cx + 100, cy + 40), start=200, end=-20, fill=PRIMARY, width=8)
    draw.rounded_rectangle((cx - 115, cy - 10, cx - 65, cy + 70), radius=18, fill=PRIMARY)
    draw.rounded_rectangle((cx + 65, cy - 10, cx + 115, cy + 70), radius=18, fill=PRIMARY)


def icon_watch(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 256
    draw.rounded_rectangle((cx - 90, cy - 110, cx + 90, cy + 110), radius=28, fill=WHITE, outline=PRIMARY, width=5)
    draw.ellipse((cx - 65, cy - 65, cx + 65, cy + 65), outline=PRIMARY, width=5)
    draw.line([(cx, cy), (cx, cy - 35)], fill=PRIMARY, width=4)
    draw.line([(cx, cy), (cx + 28, cy + 10)], fill=PRIMARY, width=4)


def icon_accessories(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 256
    draw.rounded_rectangle((cx - 100, cy - 30, cx + 100, cy + 30), radius=15, fill=PRIMARY)
    draw.rounded_rectangle((cx - 130, cy - 18, cx - 70, cy + 18), radius=8, fill=WHITE, outline=PRIMARY, width=4)
    draw.rounded_rectangle((cx + 70, cy - 18, cx + 130, cy + 18), radius=8, fill=WHITE, outline=PRIMARY, width=4)


def icon_gadgets(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 256
    draw.rounded_rectangle((cx - 80, cy - 80, cx + 20, cy + 20), radius=16, fill=PRIMARY)
    draw.rounded_rectangle((cx - 20, cy - 20, cx + 80, cy + 80), radius=16, fill=WHITE, outline=PRIMARY, width=5)


def icon_installment(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 256
    draw.rounded_rectangle((cx - 110, cy - 70, cx + 110, cy + 70), radius=20, fill=WHITE, outline=PRIMARY, width=5)
    draw.line([(cx - 70, cy + 10), (cx + 70, cy + 10)], fill=PRIMARY, width=4)
    draw.rounded_rectangle((cx - 55, cy - 35, cx - 15, cy + 5), radius=6, fill=PRIMARY)
    draw.rounded_rectangle((cx - 5, cy - 35, cx + 35, cy + 5), radius=6, fill=BG2, outline=PRIMARY, width=3)


def icon_product(draw: ImageDraw.ImageDraw) -> None:
    cx, cy = 256, 240
    draw.rounded_rectangle((cx - 90, cy - 70, cx + 90, cy + 90), radius=20, fill=WHITE, outline=PRIMARY, width=5)
    draw.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=BG2, outline=PRIMARY, width=3)


def save_category(name: str, drawer) -> None:
    img, draw = tile_base()
    drawer(draw)
    img.save(ROOT / f"cat-{name}.png", optimize=True)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    draw_hero().save(ROOT / "hero-mobile-gadgets.png", optimize=True)
    save_category("mobile", icon_mobile)
    save_category("headphones", icon_headphones)
    save_category("smartwatch", icon_watch)
    save_category("accessories", icon_accessories)
    save_category("gadgets", icon_gadgets)
    save_category("installment", icon_installment)
    img, draw = tile_base()
    icon_product(draw)
    img.save(ROOT / "product-placeholder.png", optimize=True)
    print(f"Generated assets in {ROOT}")


if __name__ == "__main__":
    main()
