#!/usr/bin/env bash
# Install official ZarinPal WooCommerce plugin on STAGING (wp_staging_app) only.
set -euo pipefail

HOST="${STAGING_SSH_HOST:-root@185.18.214.66}"
PORT="${STAGING_SSH_PORT:-22}"
CONTAINER="${STAGING_WP_CONTAINER:-wp_staging_app}"
PLUGIN_SLUG="zarinpal-woocommerce-payment-gateway"
PLUGIN_VERSION="${ZARINPAL_PLUGIN_VERSION:-5.1.1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${CONTAINER}" != "wp_staging_app" ]]; then
	echo "Refusing: STAGING_WP_CONTAINER must be wp_staging_app (got: ${CONTAINER})"
	exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 -p "${PORT}")
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
	echo "Set VPS_PASSWORD or STAGING_SSH_PRIVATE_KEY."
	exit 1
fi

cleanup() {
	if [[ -n "${KEY_FILE}" && -f "${KEY_FILE}" ]]; then
		rm -f "${KEY_FILE}"
	fi
}
trap cleanup EXIT

echo "==> Staging ZarinPal install (${PLUGIN_SLUG} ${PLUGIN_VERSION}) on ${CONTAINER}..."
"${SSH[@]}" "${HOST}" "docker ps --format '{{.Names}}' | grep -qx '${CONTAINER}'"

ensure_wp_cli() {
	"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} sh -c '\
		if command -v wp >/dev/null 2>&1; then exit 0; fi; \
		if [ -x /usr/local/bin/wp ]; then exit 0; fi; \
		curl -fsSL -o /usr/local/bin/wp https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && \
		chmod +x /usr/local/bin/wp'"
}

run_wp() {
	ensure_wp_cli
	local quoted=""
	for arg in "$@"; do
		quoted+=" $(printf '%q' "$arg")"
	done
	# shellcheck disable=SC2086
	"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} wp${quoted} --allow-root --path=/var/www/html"
}

run_wp plugin install "${PLUGIN_SLUG}" --version="${PLUGIN_VERSION}" --activate --force

echo "==> Non-secret gateway configuration..."
ensure_wp_cli
"${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} wp eval-file - --allow-root --path=/var/www/html" \
	< "${ROOT}/scripts/configure-staging-zarinpal-nonsecrets.php"

echo "==> Flush caches (staging)..."
run_wp cache flush 2>/dev/null || true

echo "Staging ZarinPal setup complete."
