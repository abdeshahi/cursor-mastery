#!/usr/bin/env python3
"""CTTEL homepage campaign art — commercial tech/editorial (no inventory silhouettes)."""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent / "assets" / "campaign"
SEED = 20260921


def _rng(seed_offset: int = 0) -> random.Random:
    return random.Random(SEED + seed_offset)


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
            draw.point(
                (x, y),
                fill=(
                    int(_lerp(c0[0], c1[0], t)),
                    int(_lerp(c0[1], c1[1], t)),
                    int(_lerp(c0[2], c1[2], t)),
                ),
            )


def _composite(base: Image.Image, overlay: Image.Image) -> Image.Image:
    return Image.alpha_composite(base.convert("RGBA"), overlay)


def _bokeh(
    img: Image.Image,
    count: int,
    palette: list[tuple[int, int, int, int]],
    blur_scale: float = 28,
    seed_offset: int = 0,
) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r = _rng(seed_offset)
    w, h = img.size
    for _ in range(count):
        cx = r.randint(-w // 8, w + w // 8)
        cy = r.randint(-h // 8, h + h // 8)
        rad = r.randint(max(w, h) // 10, max(w, h) // 2)
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=r.choice(palette))
    blur = max(4, int(max(w, h) / blur_scale))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=blur))
    return _composite(img, overlay)


def _lens_flare(img: Image.Image, cx: float, cy: float, scale: float = 1.0) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    base = min(w, h) * scale
    rings = [(base * 0.55, (147, 197, 253, 90)), (base * 0.32, (59, 130, 246, 70)), (base * 0.18, (255, 255, 255, 110))]
    for rad, col in rings:
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col)
    draw.line((cx - base * 1.2, cy, cx + base * 1.2, cy), fill=(147, 197, 253, 45), width=max(2, int(base * 0.02)))
    draw.line((cx, cy - base * 0.8, cx, cy + base * 0.8), fill=(147, 197, 253, 35), width=max(2, int(base * 0.015)))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(3, int(base * 0.04))))
    return _composite(img, overlay)


def _rim_light(img: Image.Image) -> Image.Image:
    """Soft studio edge glow (abstract product-ad lighting, not a device outline)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    draw.rounded_rectangle(
        (int(w * 0.52), int(h * 0.08), int(w * 0.94), int(h * 0.92)),
        radius=int(min(w, h) * 0.08),
        fill=(15, 23, 42, 0),
        outline=(191, 219, 254, 95),
        width=max(6, int(w * 0.008)),
    )
    draw.rounded_rectangle(
        (int(w * 0.54), int(h * 0.11), int(w * 0.92), int(h * 0.89)),
        radius=int(min(w, h) * 0.07),
        fill=(30, 58, 110, 140),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=int(w * 0.012)))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.rounded_rectangle(
        (int(w * 0.56), int(h * 0.14), int(w * 0.9), int(h * 0.86)),
        radius=int(min(w, h) * 0.06),
        fill=(56, 189, 248, 35),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(w * 0.025)))
    img = _composite(img, overlay)
    return _composite(img, glow)


def _light_streak(img: Image.Image, strength: int = 38) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    draw.polygon(
        [(w * 0.48, -h * 0.05), (w * 1.05, h * 0.32), (w * 0.72, h * 1.05), (w * 0.15, h * 0.42)],
        fill=(147, 197, 253, strength),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=w // 28))
    return _composite(img, overlay)


def _waves(img: Image.Image, color: tuple[int, int, int, int], amplitude: float = 0.04) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    for i in range(7):
        y0 = h * (0.12 + i * 0.11)
        pts = []
        for x in range(0, w + 24, 20):
            y = y0 + math.sin(x / 70 + i * 0.7) * (h * amplitude)
            pts.append((x, y))
        pts += [(w, h), (0, h)]
        alpha = max(10, color[3] - i * 5)
        draw.polygon(pts, fill=(color[0], color[1], color[2], alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=5))
    return _composite(img, overlay)


def _noise_grain(img: Image.Image, amount: int = 12, seed_offset: int = 0) -> Image.Image:
    r = _rng(seed_offset)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    px = overlay.load()
    w, h = img.size
    step = 3
    for y in range(0, h, step):
        for x in range(0, w, step):
            if r.random() > 0.65:
                v = r.randint(0, amount)
                for dy in range(step):
                    for dx in range(step):
                        if x + dx < w and y + dy < h:
                            px[x + dx, y + dy] = (255, 255, 255, v)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1))
    return _composite(img, overlay)


def hero_campaign() -> Image.Image:
    img = Image.new("RGB", (1800, 1100), (5, 12, 24))
    _gradient(img, (5, 12, 24), (17, 38, 72), 118)
    img = _bokeh(
        img,
        16,
        [(37, 99, 235, 40), (14, 165, 233, 35), (248, 250, 252, 18)],
        blur_scale=22,
        seed_offset=1,
    )
    img = _rim_light(img)
    img = _lens_flare(img, img.size[0] * 0.72, img.size[1] * 0.38, scale=0.42)
    img = _lens_flare(img, img.size[0] * 0.58, img.size[1] * 0.52, scale=0.18)
    img = _light_streak(img, strength=48)
    img = _noise_grain(img, amount=10, seed_offset=2)
    return img.convert("RGB")


def cat_mobile() -> Image.Image:
    img = Image.new("RGB", (900, 900), (8, 18, 38))
    _gradient(img, (8, 18, 38), (29, 78, 216), 135)
    img = _lens_flare(img, 620, 280, scale=0.35)
    img = _bokeh(img, 14, [(56, 189, 248, 55), (37, 99, 235, 45)], seed_offset=10)
    return img.convert("RGB")


def cat_accessories() -> Image.Image:
    img = Image.new("RGB", (900, 900), (231, 229, 228))
    _gradient(img, (245, 243, 240), (168, 162, 158), 52)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(6):
        y = 80 + i * 120
        draw.arc((-120, y - 220, 1020, y + 220), 25, 155, fill=(255, 255, 255, 70), width=22)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=10))
    img = _composite(img, overlay)
    img = _bokeh(img, 8, [(255, 255, 255, 80), (214, 211, 209, 50)], blur_scale=35, seed_offset=11)
    return img.convert("RGB")


def cat_headphones() -> Image.Image:
    img = Image.new("RGB", (900, 900), (49, 46, 129))
    _gradient(img, (49, 46, 129), (99, 102, 241), 210)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.pieslice((60, 60, 840, 840), 205, 335, fill=(196, 181, 253, 100))
    draw.pieslice((60, 60, 840, 840), 25, 155, fill=(167, 139, 250, 85))
    for i in range(8):
        y = 180 + i * 70
        draw.arc((100, y, 800, y + 400), 0, 180, fill=(224, 231, 255, 35), width=6)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=12))
    return _composite(img, overlay).convert("RGB")


def cat_smartwatch() -> Image.Image:
    img = Image.new("RGB", (900, 900), (6, 78, 59))
    _gradient(img, (6, 78, 59), (20, 184, 166), 75)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = 450, 450
    for r, a in ((320, 40), (250, 55), (180, 70), (110, 90)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(153, 246, 228, a), width=10)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=4))
    img = _composite(img, overlay)
    img = _lens_flare(img, 520, 360, scale=0.22)
    return img.convert("RGB")


def cat_used() -> Image.Image:
    img = Image.new("RGB", (900, 900), (28, 25, 23))
    _gradient(img, (28, 25, 23), (120, 53, 15), 145)
    img = _bokeh(
        img,
        16,
        [(251, 191, 36, 45), (245, 158, 11, 35), (59, 130, 246, 25)],
        seed_offset=12,
    )
    img = _light_streak(img, strength=28)
    return img.convert("RGB")


def cat_installment() -> Image.Image:
    img = Image.new("RGB", (900, 900), (224, 242, 254))
    _gradient(img, (224, 242, 254), (186, 230, 253), 100)
    img = _waves(img, (37, 99, 235, 50), amplitude=0.035)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((160, 300, 740, 560), radius=40, fill=(255, 255, 255, 150))
    draw.rounded_rectangle((210, 350, 690, 430), radius=14, fill=(37, 99, 235, 100))
    draw.rounded_rectangle((210, 450, 420, 490), radius=8, fill=(147, 197, 253, 120))
    draw.rounded_rectangle((450, 450, 620, 490), radius=8, fill=(191, 219, 254, 130))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1))
    img = _composite(img, overlay)
    return img.convert("RGB")


def used_banner() -> Image.Image:
    img = Image.new("RGB", (1400, 900), (7, 16, 32))
    _gradient(img, (7, 16, 32), (30, 41, 59), 95)
    img = _bokeh(img, 14, [(59, 130, 246, 40), (251, 191, 36, 22)], seed_offset=20)
    img = _light_streak(img, strength=32)
    img = _noise_grain(img, 8, seed_offset=21)
    return img.convert("RGB")


def installment_banner() -> Image.Image:
    img = Image.new("RGB", (1400, 820), (236, 248, 255))
    _gradient(img, (236, 248, 255), (191, 219, 254), 85)
    img = _waves(img, (59, 130, 246, 55), amplitude=0.038)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((180, 220, 620, 620), radius=48, fill=(255, 255, 255, 130))
    draw.rounded_rectangle((240, 300, 560, 380), radius=16, fill=(37, 99, 235, 90))
    draw.ellipse((780, 260, 1100, 580), fill=(147, 197, 253, 80))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=8))
    img = _composite(img, overlay)
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
