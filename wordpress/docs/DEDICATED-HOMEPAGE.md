# CTTEL dedicated homepage (rebuild)

Single presentation source for the static front page — **not** Gutenberg blocks + shortcodes.

## Activate (staging/local)

1. Deploy mu-plugins (includes `cttel-homepage.php`, `cttel-homepage-render.php`, `cttel-homepage.css`, `templates/cttel-front-page.php`).
2. Run:

```bash
./scripts/apply-dedicated-homepage.sh
```

3. Upload **real** retail photography to WordPress media (not `cttel-*` preview PNGs).
4. Set options: `cttel_hero_media_id`, category thumbnails, product featured images.

Preview line-art assets (`cttel-hero-mobile-gadgets`, `product-placeholder`, etc.) are **ignored** on the dedicated homepage.

## Preserve (unchanged)

Mobile hamburger (right), off-canvas, WooCommerce, Used Phone Request, Enamad, infra.
