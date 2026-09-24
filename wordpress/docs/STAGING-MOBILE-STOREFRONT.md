# Staging deploy — CTTEL mobile storefront (Hamrahtel-style UX)

**Target:** https://staging.cttel.ir only  
**Container:** `wp_staging_app` (default `STAGING_WP_CONTAINER`)  
**Host path:** `/opt/cttel-wordpress-staging/` (reference only — sync uses Docker exec)

Never run these steps against production (`wp_app`, `cttel.ir`).

## What gets synced

Mu-plugins and templates under `wordpress/mu-plugins/`:

| File | Role |
|------|------|
| `cttel-homepage.php` | Disables legacy mockup; boots mobile storefront |
| `cttel-mobile-storefront*.php` | Shell, home, categories hub |
| `cttel-mobile-storefront.css` | Mobile-first layout |
| `templates/cttel-mobile-front.php` | Front page template |
| `templates/cttel-categories-hub.php` | `/dastebandi/` split category UX |
| `cttel-design-system.php`, `cttel-quick-categories.php` | Tokens + category helpers |

Legacy files (`cttel-homepage-render.php`, `cttel-homepage.css`, `cttel-home-mockup.css`) are **not** deployed by the updated sync script.

## Manual sync (from repo)

```bash
export STAGING_WP_CONTAINER=wp_staging_app
export VPS_PASSWORD='…'   # or STAGING_SSH_PRIVATE_KEY
cd wordpress && ./scripts/sync-staging-homepage.sh
```

The script **fails closed** if `STAGING_WP_CONTAINER` is not `wp_staging_app` or if the container is missing.

## After deploy

1. Confirm static front page is still set in **Settings → Reading**.
2. Open `/dastebandi/` (categories hub). If 404, run inside staging container:
   `wp rewrite flush --allow-root`
3. Visual QA at 390px width: home search, bottom nav, category split panel.

## GitHub Actions

Workflow `.github/workflows/deploy-staging-homepage.yml` runs the same script on push to the storefront branch (requires `VPS_PASSWORD` or `STAGING_SSH_PRIVATE_KEY` secret).
