#!/bin/sh
# Upload CTTEL brand placeholders and wire Hero / categories / product fallback.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="${ROOT}/assets/brand"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

import_media() {
  file="$1"
  title="$2"
  slug="$3"
  base="$(basename "${file}")"
  existing="$(WP db query "SELECT ID FROM wp_posts WHERE post_type='attachment' AND post_title='${title}' LIMIT 1;" --skip-column-names 2>/dev/null | tr -d ' \n')"
  if [ -n "${existing}" ] && [ "${existing}" != "0" ]; then
    echo "${existing}"
    return 0
  fi
  docker cp "${file}" "wp_app:/var/www/html/${base}"
  id="$(WP media import "/var/www/html/${base}" --title="${title}" --post_name="${slug}" --porcelain)"
  docker exec wp_app rm -f "/var/www/html/${base}"
  echo "${id}"
}

if [ ! -f "${ASSETS}/hero-mobile-gadgets.png" ]; then
  echo "==> Generate brand PNGs..."
  python3 "${ROOT}/scripts/generate-brand-assets.py"
fi

echo "==> Import brand images..."
HERO_ID="$(import_media "${ASSETS}/hero-mobile-gadgets.png" "CTTEL Hero Mobile Gadgets" "cttel-hero-mobile-gadgets")"
PRODUCT_ID="$(import_media "${ASSETS}/product-placeholder.png" "CTTEL Product Placeholder" "cttel-product-placeholder")"
MOBILE_ID="$(import_media "${ASSETS}/cat-mobile.png" "CTTEL Category Mobile" "cttel-cat-mobile")"
HEAD_ID="$(import_media "${ASSETS}/cat-headphones.png" "CTTEL Category Headphones" "cttel-cat-headphones")"
WATCH_ID="$(import_media "${ASSETS}/cat-smartwatch.png" "CTTEL Category Smartwatch" "cttel-cat-smartwatch")"
ACC_ID="$(import_media "${ASSETS}/cat-accessories.png" "CTTEL Category Accessories" "cttel-cat-accessories")"
GAD_ID="$(import_media "${ASSETS}/cat-gadgets.png" "CTTEL Category Gadgets" "cttel-cat-gadgets")"
INST_ID="$(import_media "${ASSETS}/cat-installment.png" "CTTEL Category Installment" "cttel-cat-installment")"

echo "==> Options + category thumbnails..."
WP option update cttel_product_placeholder_id "${PRODUCT_ID}"
WP theme mod set cttel_installment_card_image "${INST_ID}" 2>/dev/null || true
WP term meta update 18 thumbnail_id "${MOBILE_ID}"
WP term meta update 19 thumbnail_id "${HEAD_ID}"
WP term meta update 20 thumbnail_id "${WATCH_ID}"
WP term meta update 21 thumbnail_id "${ACC_ID}"
WP term meta update 22 thumbnail_id "${GAD_ID}"

echo "==> Homepage hero..."
docker cp "${ROOT}/scripts/seed-brand-images.php" wp_app:/var/www/html/seed-brand-images.php
WP eval-file /var/www/html/seed-brand-images.php "${HERO_ID}"
docker exec wp_app rm -f /var/www/html/seed-brand-images.php

# Sync repo homepage template for future deploys (local file uses attachment id comment only in DB)
WP cache flush 2>/dev/null || true
echo "Done. hero=${HERO_ID} product_placeholder=${PRODUCT_ID}"
