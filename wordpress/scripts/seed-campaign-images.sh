#!/bin/sh
# Import premium campaign media for dedicated homepage (local/staging).
# On staging after deploy: REFRESH_CAMPAIGN_MEDIA=1 ./scripts/seed-campaign-images.sh
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="${ROOT}/assets/campaign"
cd "${ROOT}"

WP() {
  sudo docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

import_media() {
  file="$1"
  title="$2"
  slug="$3"
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
  sudo docker cp "${file}" "wp_app:/var/www/html/${base}"
  id="$(WP media import "/var/www/html/${base}" --title="${title}" --post_name="${slug}" --porcelain)"
  sudo docker exec wp_app rm -f "/var/www/html/${base}"
  echo "${id}"
}

echo "==> Generate campaign PNGs..."
python3 "${ROOT}/scripts/generate-campaign-assets.py"
REFRESH_CAMPAIGN_MEDIA=1
export REFRESH_CAMPAIGN_MEDIA

echo "==> Import campaign images..."
HERO_ID="$(import_media "${ASSETS}/hero-campaign.png" "CTTEL Campaign Hero" "cttel-campaign-hero")"
MOBILE_ID="$(import_media "${ASSETS}/cat-mobile.png" "CTTEL Campaign Mobile" "cttel-campaign-cat-mobile")"
ACC_ID="$(import_media "${ASSETS}/cat-accessories.png" "CTTEL Campaign Accessories" "cttel-campaign-cat-accessories")"
HEAD_ID="$(import_media "${ASSETS}/cat-headphones.png" "CTTEL Campaign Headphones" "cttel-campaign-cat-headphones")"
WATCH_ID="$(import_media "${ASSETS}/cat-smartwatch.png" "CTTEL Campaign Smartwatch" "cttel-campaign-cat-smartwatch")"
USED_CAT_ID="$(import_media "${ASSETS}/cat-used.png" "CTTEL Campaign Used Phones" "cttel-campaign-cat-used")"
INST_CAT_ID="$(import_media "${ASSETS}/cat-installment.png" "CTTEL Campaign Installment" "cttel-campaign-cat-installment")"
USED_BANNER_ID="$(import_media "${ASSETS}/used-banner.png" "CTTEL Campaign Used Banner" "cttel-campaign-used-banner")"
INST_BANNER_ID="$(import_media "${ASSETS}/installment-banner.png" "CTTEL Campaign Installment Banner" "cttel-campaign-installment-banner")"

echo "==> Wire homepage options..."
WP option update cttel_hero_media_id "${HERO_ID}"
WP option update cttel_used_banner_media_id "${USED_BANNER_ID}"
WP option update cttel_installment_campaign_media_id "${INST_BANNER_ID}"
WP option update cttel_mosaic_used_media_id "${USED_CAT_ID}"
WP option update cttel_mosaic_installment_media_id "${INST_CAT_ID}"

echo "==> Category thumbnails..."
for pair in "mobile:${MOBILE_ID}" "headphones:${HEAD_ID}" "smartwatch:${WATCH_ID}" "accessories:${ACC_ID}"; do
  slug="${pair%%:*}"
  img_id="${pair##*:}"
  tid="$(WP term list product_cat --slug="${slug}" --field=term_id 2>/dev/null | head -1)"
  if [ -n "${tid}" ]; then
    WP term meta update "${tid}" thumbnail_id "${img_id}" 2>/dev/null || true
  fi
done

echo "==> Store currency (Iranian storefront)..."
WP option update woocommerce_currency IRT
WP option update woocommerce_currency_pos right_space

WP cache flush 2>/dev/null || true
echo "Done. hero=${HERO_ID} currency=IRT"
