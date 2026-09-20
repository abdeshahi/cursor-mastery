# CTTEL Homepage v2 — Design Review (not deployed)

## Activate locally for WordPress preview

1. Copy mu-plugins: `cttel-design-system.php`, `cttel-home-sections.php`
2. Update homepage content from `content/homepage-blocks.html` (do **not** run on production until approved)
3. Flush caches

## Static mock (no WordPress)

```bash
cd wordpress/design-review
python3 -m http.server 8765
```

Open `http://127.0.0.1:8765/preview.html`

## Out of scope (unchanged)

- Mobile RTL header / off-canvas mu-plugins
- Enamad, used-phone request backend, WooCommerce orders, n8n, Divar, infra
