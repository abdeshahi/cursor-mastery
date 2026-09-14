#!/bin/sh
# Deploy WooCommerce-synced quick category cards (mu-plugin + homepage shortcode).
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

echo "==> Deploy mu-plugin..."
docker exec wp_app mkdir -p /var/www/html/wp-content/mu-plugins
docker cp "${ROOT}/mu-plugins/cttel-quick-categories.php" \
  wp_app:/var/www/html/wp-content/mu-plugins/cttel-quick-categories.php

echo "==> Sync homepage quick categories section..."
CONTENT="$(cat "${ROOT}/content/homepage-blocks.html")"
WP post update 24 --post_content="${CONTENT}" --post_status=publish

echo "==> Flush caches..."
WP cache flush 2>/dev/null || true

echo "Quick categories deployed."
