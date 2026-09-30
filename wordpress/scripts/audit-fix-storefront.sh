#!/bin/sh
# Final storefront audit fixes — WordPress only (no infrastructure changes).
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

echo "==> Deploy mu-plugin (Toman currency)..."
docker exec wp_app mkdir -p /var/www/html/wp-content/mu-plugins
docker cp "${ROOT}/mu-plugins/cttel-store.php" wp_app:/var/www/html/wp-content/mu-plugins/cttel-store.php

echo "==> Apply Blocksy header/footer/typography defaults..."
docker cp "${ROOT}/scripts/blocksy-audit-config.php" wp_app:/var/www/html/blocksy-audit-config.php
docker compose run --rm --entrypoint wp wp-init eval-file /var/www/html/blocksy-audit-config.php --allow-root
docker exec wp_app rm -f /var/www/html/blocksy-audit-config.php

echo "==> Footer widgets (editable: Appearance → Widgets)..."
WP widget list ct-footer-sidebar-1 2>/dev/null | grep -q text || \
  WP widget add text ct-footer-sidebar-1 1 --title='درباره CTTEL' \
    --text='<p>فروشگاه تخصصی تجهیزات مخابراتی CTTEL</p><p>تلفن: 021-00000000</p><p>آدرس: تهران، ایران</p>'

echo "==> Remove unused default plugins..."
WP plugin delete hello 2>/dev/null || true

echo "==> WooCommerce currency (Toman via mu-plugin)..."
WP option update woocommerce_currency 'IRT' 2>/dev/null || true

echo "==> Ensure lazy-loading (WordPress native)..."
WP option update wp_lazy_loading_enabled 1 2>/dev/null || true

echo "==> Flush caches..."
WP cache flush 2>/dev/null || true

echo "Audit fix complete."
