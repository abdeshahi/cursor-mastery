#!/usr/bin/env bash
# Sync CTTEL mobile storefront mu-plugins to STAGING only (wp_staging_app). Never production.
set -euo pipefail

HOST="${STAGING_SSH_HOST:-root@185.18.214.66}"
PORT="${STAGING_SSH_PORT:-22}"
CONTAINER="${STAGING_WP_CONTAINER:-wp_staging_app}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${CONTAINER}" != "wp_staging_app" ]]; then
	echo "Refusing sync: STAGING_WP_CONTAINER must be wp_staging_app (got: ${CONTAINER})"
	exit 1
fi

MU_FILES=(
	cttel-staging-home-sync.php
	cttel-homepage.php
	cttel-mobile-storefront.php
	cttel-mobile-storefront-shell.php
	cttel-mobile-storefront-home.php
	cttel-mobile-storefront-categories.php
	cttel-mobile-storefront-archive.php
	cttel-mobile-storefront-single.php
	cttel-mobile-storefront-cart-checkout.php
	cttel-staging-wc-readiness.php
	cttel-staging-shipping-postpaid.php
	cttel-staging-online-payment.php
	cttel-mobile-storefront-assets.php
	cttel-ms-seed-product-photos.php
	cttel-mobile-storefront.css
	cttel-design-system.php
	cttel-quick-categories.php
	cttel-product-cards.php
	cttel-footer-branding.php
	cttel-blocksy-mobile-offcanvas.php
	cttel-blocksy-mobile-header.php
	cttel-store.php
	cttel-catalog.php
	cttel-storefront-product-card.php
	cttel-storefront-search.php
)

TEMPLATE_FILES=(
	templates/cttel-mobile-front.php
	templates/cttel-categories-hub.php
	templates/content-product-ms.php
	templates/cttel-ms-single-product-reviews.php
	templates/cttel-ms-cart-empty.php
)

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -p "${PORT}")
KEY_FILE=""
if [[ -n "${STAGING_SSH_PRIVATE_KEY:-}" ]]; then
	KEY_FILE="$(mktemp)"
	printf '%s\n' "${STAGING_SSH_PRIVATE_KEY}" > "${KEY_FILE}"
	chmod 600 "${KEY_FILE}"
	SSH=(ssh -i "${KEY_FILE}" "${SSH_OPTS[@]}")
elif [[ -n "${VPS_PASSWORD:-}" ]]; then
	command -v sshpass >/dev/null 2>&1 || { echo "Install sshpass or use STAGING_SSH_PRIVATE_KEY."; exit 1; }
	SSH=(sshpass -p "${VPS_PASSWORD}" ssh "${SSH_OPTS[@]}")
else
	echo "Set VPS_PASSWORD or STAGING_SSH_PRIVATE_KEY to deploy."
	exit 1
fi

cleanup() {
	if [[ -n "${KEY_FILE}" && -f "${KEY_FILE}" ]]; then
		rm -f "${KEY_FILE}"
	fi
}
trap cleanup EXIT

echo "==> Staging sync to ${HOST} (container ${CONTAINER})..."
if ! "${SSH[@]}" "${HOST}" "docker ps --format '{{.Names}}' | grep -qx '${CONTAINER}'"; then
	echo "Staging container ${CONTAINER} not found on ${HOST}. Aborting (fail closed)."
	exit 1
fi

"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} mkdir -p /var/www/html/wp-content/mu-plugins/templates"

for f in "${MU_FILES[@]}"; do
	src="${ROOT}/mu-plugins/${f}"
	if [[ ! -f "${src}" ]]; then
		echo "Skip missing ${f}"
		continue
	fi
	echo "  ${f}"
	"${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} tee /var/www/html/wp-content/mu-plugins/${f}" < "${src}" >/dev/null
done

for rel in "${TEMPLATE_FILES[@]}"; do
	src="${ROOT}/mu-plugins/${rel}"
	if [[ ! -f "${src}" ]]; then
		echo "Skip missing ${rel}"
		continue
	fi
	echo "  ${rel}"
	"${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} tee /var/www/html/wp-content/mu-plugins/${rel}" < "${src}" >/dev/null
done

ASSETS_DIR="${ROOT}/mu-plugins/assets/cttel-ms"
if [[ -d "${ASSETS_DIR}" ]]; then
	echo "==> Sync mu-plugins/assets/cttel-ms/ ..."
	while IFS= read -r -d '' asset; do
		rel="${asset#${ROOT}/mu-plugins/}"
		echo "  ${rel}"
		"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} mkdir -p /var/www/html/wp-content/mu-plugins/$(dirname "${rel}")"
		"${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} tee /var/www/html/wp-content/mu-plugins/${rel}" < "${asset}" >/dev/null
	done < <(find "${ASSETS_DIR}" -type f -print0)
fi

echo "==> Flush rewrite rules + caches (staging)..."
"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} wp rewrite flush --allow-root 2>/dev/null || true"
"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} wp cache flush --allow-root 2>/dev/null || true"

echo "Staging mobile storefront mu-plugins synced."
