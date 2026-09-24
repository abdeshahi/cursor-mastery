#!/bin/sh
# Switch static front page to dedicated CTTEL homepage template (empty block content).
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

FRONT_ID="$(WP option get page_on_front 2>/dev/null | tr -d ' \n')"
if [ -z "${FRONT_ID}" ] || [ "${FRONT_ID}" = "0" ]; then
  FRONT_ID="$(WP post list --post_type=page --name=home --field=ID 2>/dev/null | head -1)"
fi
if [ -z "${FRONT_ID}" ]; then
  FRONT_ID="$(WP post create --post_type=page --post_title='صفحه اصلی' --post_name=home --post_status=publish --post_content='' --porcelain)"
fi

WP post update "${FRONT_ID}" --post_content='' --post_status=publish
WP post meta update "${FRONT_ID}" _wp_page_template cttel-front-page.php
WP option update show_on_front page
WP option update page_on_front "${FRONT_ID}"
WP cache flush 2>/dev/null || true

echo "Dedicated homepage active on page ID ${FRONT_ID}"
