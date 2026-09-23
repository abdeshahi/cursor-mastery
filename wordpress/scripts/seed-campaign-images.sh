#!/bin/sh
# Import owner-approved homepage media (PR #17 deterministic workflow).
# Staging: REFRESH_CAMPAIGN_MEDIA=1 ./scripts/seed-campaign-images.sh
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="${ROOT}/assets/owner-approved"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

import_media() {
  file="$1"
  title="$2"
  slug="$3"
  if [ ! -f "${file}" ]; then
    echo "Missing asset: ${file}" >&2
    exit 1
  fi
  base="$(basename "${file}")"
  existing="$(WP db query "SELECT ID FROM wp_posts WHERE post_type='attachment' AND post_name='${slug}' LIMIT 1;" --skip-column-names 2>/dev/null | tr -d ' \n')"
  if [ -n "${existing}" ] && [ "${existing}" != "0" ]; then
    if [ "${REFRESH_CAMPAIGN_MEDIA:-0}" = "1" ]; then
      WP post delete "${existing}" --force >/dev/null 2>&1 || true
    else
      echo "${existing}"
      return 0
    fi
  fi
  docker cp "${file}" "wp_app:/var/www/html/${base}"
  id="$(WP media import "/var/www/html/${base}" --title="${title}" --post_name="${slug}" --porcelain)"
  docker exec wp_app rm -f "/var/www/html/${base}"
  echo "${id}"
}

REFRESH_CAMPAIGN_MEDIA="${REFRESH_CAMPAIGN_MEDIA:-1}"
export REFRESH_CAMPAIGN_MEDIA

echo "==> Import owner-approved WebP assets from ${ASSETS}..."

HERO_ID="$(import_media "${ASSETS}/futuristic_blue_tech_showcase.webp" "CTTEL Hero — Blue Tech Showcase" "cttel-campaign-hero")"
MOBILE_ID="$(import_media "${ASSETS}/futuristic_blue_smartphone_showcase.webp" "CTTEL Category Mobile" "cttel-campaign-cat-mobile")"
ACC_ID="$(import_media "${ASSETS}/futuristic_tech_accessories_still_life.webp" "CTTEL Category Accessories" "cttel-campaign-cat-accessories")"
HEAD_ID="$(import_media "${ASSETS}/futuristic_purple_earbuds_studio_render.webp" "CTTEL Category Headphones" "cttel-campaign-cat-headphones")"
WATCH_ID="$(import_media "${ASSETS}/futuristic_teal_smartwatch_hero_scene.webp" "CTTEL Category Smartwatch" "cttel-campaign-cat-smartwatch")"
USED_ID="$(import_media "${ASSETS}/certified_smartphone_golden_halo.webp" "CTTEL Used Phone Campaign" "cttel-campaign-cat-used")"
INST_ID="$(import_media "${ASSETS}/futuristic_contactless_payment_showcase.webp" "CTTEL Installment Campaign" "cttel-campaign-cat-installment")"

echo "==> Wire homepage options..."
WP option update cttel_hero_media_id "${HERO_ID}"
WP option update cttel_used_banner_media_id "${USED_ID}"
WP option update cttel_installment_campaign_media_id "${INST_ID}"
WP option update cttel_mosaic_used_media_id "${USED_ID}"
WP option update cttel_mosaic_installment_media_id "${INST_ID}"

echo "==> Category thumbnails..."
for pair in "mobile:${MOBILE_ID}" "headphones:${HEAD_ID}" "smartwatch:${WATCH_ID}" "accessories:${ACC_ID}"; do
  slug="${pair%%:*}"
  img_id="${pair##*:}"
  tid="$(WP term list product_cat --slug="${slug}" --field=term_id 2>/dev/null | head -1)"
  if [ -n "${tid}" ]; then
    WP term meta update "${tid}" thumbnail_id "${img_id}" 2>/dev/null || true
  fi
done

WP cache flush 2>/dev/null || true
echo "Done. hero=${HERO_ID} used=${USED_ID} installment=${INST_ID}"
