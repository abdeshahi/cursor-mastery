#!/usr/bin/env python3
"""CTTEL homepage campaign art v3 — premium retail / fintech editorial (no inventory claims)."""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent / "assets" / "campaign"
SEED = 20260922


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
        rad = r.randint(max(w, h) // 12, max(w, h) // 2)
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=r.choice(palette))
    blur = max(4, int(max(w, h) / blur_scale))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=blur))
    return _composite(img, overlay)


def _lens_flare(img: Image.Image, cx: float, cy: float, scale: float = 1.0) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    base = min(img.size[0], img.size[1]) * scale
    rings = [
        (base * 0.58, (147, 197, 253, 100)),
        (base * 0.34, (59, 130, 246, 80)),
        (base * 0.16, (255, 255, 255, 130)),
    ]
    for rad, col in rings:
        draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col)
    draw.line((cx - base * 1.3, cy, cx + base * 1.3, cy), fill=(191, 219, 254, 55), width=max(2, int(base * 0.018)))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(3, int(base * 0.035))))
    return _composite(img, overlay)


def _macro_lens_stack(img: Image.Image, cx: float, cy: float, scale: float = 0.5) -> Image.Image:
    """Camera-lens macro mood (abstract, not a product photo)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    base = min(img.size[0], img.size[1]) * scale
    for i, (mult, alpha) in enumerate(((0.95, 70), (0.72, 90), (0.5, 110), (0.28, 130), (0.12, 150))):
        r = base * mult
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(226, 232, 240, alpha), width=max(2, 6 - i))
    draw.ellipse((cx - base * 0.08, cy - base * 0.08, cx + base * 0.08, cy + base * 0.08), fill=(248, 250, 252, 200))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=int(base * 0.02)))
    return _composite(img, overlay)


def _studio_slab_glow(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    draw.rounded_rectangle(
        (int(w * 0.48), int(h * 0.06), int(w * 0.96), int(h * 0.94)),
        radius=int(min(w, h) * 0.07),
        fill=(12, 22, 42, 180),
    )
    draw.rounded_rectangle(
        (int(w * 0.5), int(h * 0.09), int(w * 0.94), int(h * 0.91)),
        radius=int(min(w, h) * 0.06),
        fill=(30, 64, 120, 90),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=int(w * 0.014)))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.rounded_rectangle(
        (int(w * 0.52), int(h * 0.12), int(w * 0.92), int(h * 0.88)),
        radius=int(min(w, h) * 0.05),
        fill=(125, 211, 252, 45),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(w * 0.022)))
    return _composite(_composite(img, overlay), glow)


def _light_streak(img: Image.Image, strength: int = 42) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    draw.polygon(
        [(w * 0.42, -h * 0.08), (w * 1.08, h * 0.28), (w * 0.68, h * 1.08), (w * 0.08, h * 0.38)],
        fill=(191, 219, 254, strength),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=w // 26))
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


def _nfc_rings(img: Image.Image, cx: float, cy: float) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i, r in enumerate((220, 170, 120, 70)):
        draw.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(37, 99, 235, 90 - i * 15), width=8)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=3))
    return _composite(img, overlay)


def _finish(img: Image.Image, contrast: float = 1.08, color: float = 1.06) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(color)
    return img


def hero_campaign() -> Image.Image:
    img = Image.new("RGB", (1920, 1200), (4, 10, 22))
    _gradient(img, (4, 10, 22), (15, 35, 68), 115)
    img = _bokeh(img, 14, [(37, 99, 235, 45), (14, 165, 233, 38), (255, 255, 255, 22)], blur_scale=20, seed_offset=1)
    img = _studio_slab_glow(img)
    img = _macro_lens_stack(img, img.size[0] * 0.74, img.size[1] * 0.42, scale=0.48)
    img = _lens_flare(img, img.size[0] * 0.74, img.size[1] * 0.42, scale=0.38)
    img = _light_streak(img, strength=52)
    return _finish(img.convert("RGB"), 1.12, 1.08)


def cat_mobile() -> Image.Image:
    img = Image.new("RGB", (960, 960), (6, 14, 32))
    _gradient(img, (6, 14, 32), (37, 99, 235), 130)
    img = _macro_lens_stack(img, 640, 320, scale=0.38)
    img = _lens_flare(img, 640, 320, scale=0.28)
    return _finish(img.convert("RGB"), 1.1, 1.05)


def cat_accessories() -> Image.Image:
    img = Image.new("RGB", (960, 960), (250, 247, 242))
    _gradient(img, (255, 252, 247), (214, 207, 196), 48)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(7):
        y = 60 + i * 110
        draw.arc((-140, y - 240, 1100, y + 240), 22, 158, fill=(255, 255, 255, 85), width=26)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=11))
    img = _composite(img, overlay)
    img = _bokeh(img, 6, [(255, 255, 255, 90), (231, 229, 228, 60)], blur_scale=38, seed_offset=11)
    return _finish(img.convert("RGB"), 1.05, 1.02)


def cat_headphones() -> Image.Image:
    img = Image.new("RGB", (960, 960), (30, 27, 75))
    _gradient(img, (30, 27, 75), (55, 48, 163), 205)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.pieslice((40, 40, 920, 920), 200, 340, fill=(167, 139, 250, 110))
    draw.pieslice((40, 40, 920, 920), 20, 160, fill=(129, 140, 248, 95))
    for i in range(10):
        y = 160 + i * 65
        draw.arc((80, y, 880, y + 420), 0, 180, fill=(224, 231, 255, 40), width=5)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=10))
    return _finish(_composite(img, overlay).convert("RGB"), 1.08, 1.1)


def cat_smartwatch() -> Image.Image:
    img = Image.new("RGB", (960, 960), (15, 47, 42))
    _gradient(img, (15, 47, 42), (13, 148, 136), 80)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = 480, 480
    for r, a in ((340, 45), (270, 60), (200, 75), (130, 95)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(153, 246, 228, a), width=11)
    draw.rectangle((cx - 55, cy - 140, cx + 55, cy + 140), fill=(45, 212, 191, 35))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=5))
    img = _composite(img, overlay)
    img = _lens_flare(img, 540, 400, scale=0.2)
    return _finish(img.convert("RGB"), 1.08, 1.08)


def cat_used() -> Image.Image:
    img = Image.new("RGB", (960, 960), (24, 22, 20))
    _gradient(img, (24, 22, 20), (146, 64, 14), 150)
    img = _bokeh(img, 18, [(251, 191, 36, 55), (217, 119, 6, 40), (148, 163, 184, 25)], seed_offset=12)
    img = _light_streak(img, strength=34)
    return _finish(img.convert("RGB"), 1.1, 1.06)


def cat_installment() -> Image.Image:
    img = Image.new("RGB", (960, 960), (224, 242, 254))
    _gradient(img, (240, 249, 255), (186, 230, 253), 95)
    img = _waves(img, (37, 99, 235, 55), amplitude=0.032)
    img = _nfc_rings(img, 680, 420)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((120, 340, 520, 620), radius=36, fill=(255, 255, 255, 140))
    draw.line([(160, 420), (480, 420)], fill=(37, 99, 235, 100), width=6)
    draw.line([(160, 480), (380, 480)], fill=(147, 197, 253, 120), width=6)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1))
    return _finish(_composite(img, overlay).convert("RGB"), 1.04, 1.05)


def used_banner() -> Image.Image:
    img = Image.new("RGB", (1500, 960), (12, 10, 9))
    _gradient(img, (12, 10, 9), (68, 45, 20), 100)
    img = _bokeh(img, 16, [(251, 191, 36, 50), (245, 158, 11, 35), (59, 130, 246, 20)], seed_offset=20)
    img = _studio_slab_glow(img)
    img = _light_streak(img, strength=36)
    return _finish(img.convert("RGB"), 1.1, 1.08)


def installment_banner() -> Image.Image:
    img = Image.new("RGB", (1500, 880), (236, 248, 255))
    _gradient(img, (248, 252, 255), (191, 219, 254), 78)
    img = _waves(img, (59, 130, 246, 50), amplitude=0.036)
    img = _nfc_rings(img, 1050, 440)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for x, y in ((220, 280), (320, 380), (420, 300)):
        draw.rounded_rectangle((x, y, x + 280, y + 180), radius=28, fill=(255, 255, 255, 110))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=6))
    return _finish(_composite(img, overlay).convert("RGB"), 1.05, 1.06)


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
