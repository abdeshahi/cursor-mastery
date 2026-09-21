#!/usr/bin/env python3
"""Premium campaign PNGs for CTTEL homepage (abstract / editorial — no inventory silhouettes)."""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent / "assets" / "campaign"
SEED = 20260921


def _rng() -> random.Random:
    return random.Random(SEED)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _gradient(img: Image.Image, c0: tuple[int, int, int], c1: tuple[int, int, int], angle_deg: float = 90) -> None:
    w, h = img.size
    draw = ImageDraw.Draw(img)
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    for y in range(h):
        for x in range(w):
            t = (x / max(w - 1, 1) * dx + y / max(h - 1, 1) * dy) * 0.5 + 0.5
            t = max(0.0, min(1.0, t))
            r = int(_lerp(c0[0], c1[0], t))
            g = int(_lerp(c0[1], c1[1], t))
            b = int(_lerp(c0[2], c1[2], t))
            draw.point((x, y), fill=(r, g, b))


def _bokeh(img: Image.Image, count: int, palette: list[tuple[int, int, int, int]]) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r = _rng()
    w, h = img.size
    for _ in range(count):
        cx = r.randint(-w // 10, w + w // 10)
        cy = r.randint(-h // 10, h + h // 10)
        rad = r.randint(max(w, h) // 8, max(w, h) // 3)
        color = r.choice(palette)
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(w, h) // 28))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _light_streak(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    draw.polygon(
        [(w * 0.55, -h * 0.1), (w * 1.1, h * 0.35), (w * 0.75, h * 1.1), (w * 0.2, h * 0.45)],
        fill=(147, 197, 253, 38),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=w // 32))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _waves(img: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    for i in range(6):
        y0 = h * (0.15 + i * 0.12)
        pts = []
        for x in range(0, w + 20, 24):
            y = y0 + math.sin(x / 80 + i) * (h * 0.04)
            pts.append((x, y))
        pts += [(w, h), (0, h)]
        draw.polygon(pts, fill=(color[0], color[1], color[2], max(12, color[3] - i * 4)))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=6))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def hero_campaign() -> Image.Image:
    img = Image.new("RGB", (1600, 1000), (7, 21, 38))
    _gradient(img, (7, 21, 38), (21, 45, 82), 125)
    img = _bokeh(
        img,
        28,
        [
            (37, 99, 235, 55),
            (59, 130, 246, 45),
            (147, 197, 253, 35),
            (15, 23, 42, 80),
        ],
    )
    img = _light_streak(img)
    return img.convert("RGB")


def cat_mobile() -> Image.Image:
    img = Image.new("RGB", (800, 800), (11, 31, 58))
    _gradient(img, (11, 31, 58), (30, 64, 110), 140)
    img = _bokeh(img, 22, [(56, 189, 248, 50), (37, 99, 235, 40), (248, 250, 252, 25)])
    return img.convert("RGB")


def cat_accessories() -> Image.Image:
    img = Image.new("RGB", (800, 800), (55, 65, 81))
    _gradient(img, (75, 85, 99), (156, 163, 175), 45)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(5):
        y = 120 + i * 130
        draw.arc((-100, y - 200, 900, y + 200), 20, 160, fill=(248, 250, 252, 35), width=18)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=8))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def cat_headphones() -> Image.Image:
    img = Image.new("RGB", (800, 800), (30, 41, 59))
    _gradient(img, (30, 41, 59), (71, 85, 105), 200)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.pieslice((80, 80, 720, 720), 200, 340, fill=(148, 163, 184, 90))
    draw.pieslice((80, 80, 720, 720), 20, 160, fill=(148, 163, 184, 70))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=14))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def cat_smartwatch() -> Image.Image:
    img = Image.new("RGB", (800, 800), (15, 23, 42))
    _gradient(img, (15, 23, 42), (51, 65, 85), 90)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = 400, 400
    for r in (280, 220, 160):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(96, 165, 250, 55), width=8)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=6))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def cat_used() -> Image.Image:
    img = Image.new("RGB", (800, 800), (7, 21, 38))
    _gradient(img, (7, 21, 38), (29, 78, 216), 160)
    img = _bokeh(img, 18, [(250, 204, 21, 35), (59, 130, 246, 45), (248, 250, 252, 20)])
    return img.convert("RGB")


def cat_installment() -> Image.Image:
    img = Image.new("RGB", (800, 800), (219, 234, 254))
    _gradient(img, (219, 234, 254), (191, 219, 254), 110)
    img = _waves(img, (37, 99, 235, 55))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((140, 280, 660, 520), radius=36, fill=(255, 255, 255, 120))
    draw.rounded_rectangle((180, 320, 620, 380), radius=12, fill=(37, 99, 235, 80))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=2))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def used_banner() -> Image.Image:
    img = Image.new("RGB", (1200, 800), (7, 21, 38))
    _gradient(img, (7, 21, 38), (15, 45, 82), 100)
    img = _bokeh(img, 20, [(59, 130, 246, 50), (148, 163, 184, 30)])
    img = _light_streak(img)
    return img.convert("RGB")


def installment_banner() -> Image.Image:
    img = Image.new("RGB", (1200, 700), (239, 246, 255))
    _gradient(img, (239, 246, 255), (219, 234, 254), 70)
    img = _waves(img, (59, 130, 246, 45))
    return img.convert("RGB")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    hero_campaign().save(ROOT / "hero-campaign.png", optimize=True)
    cat_mobile().save(ROOT / "cat-mobile.png", optimize=True)
    cat_accessories().save(ROOT / "cat-accessories.png", optimize=True)
    cat_headphones().save(ROOT / "cat-headphones.png", optimize=True)
    cat_smartwatch().save(ROOT / "cat-smartwatch.png", optimize=True)
    cat_used().save(ROOT / "cat-used.png", optimize=True)
    cat_installment().save(ROOT / "cat-installment.png", optimize=True)
    used_banner().save(ROOT / "used-banner.png", optimize=True)
    installment_banner().save(ROOT / "installment-banner.png", optimize=True)
    print(f"Generated campaign assets in {ROOT}")


if __name__ == "__main__":
    main()
