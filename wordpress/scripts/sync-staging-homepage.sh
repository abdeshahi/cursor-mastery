#!/usr/bin/env bash
# Sync dedicated homepage mu-plugins to staging VPS (staging.cttel.ir). Production-safe: mu-plugins only.
set -euo pipefail

HOST="${STAGING_SSH_HOST:-root@185.18.214.66}"
PORT="${STAGING_SSH_PORT:-22}"
CONTAINER="${STAGING_WP_CONTAINER:-wp_app}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MU_FILES=(
	cttel-homepage.php
	cttel-homepage-render.php
	cttel-homepage.css
	cttel-home-mockup.css
	cttel-design-system.php
	cttel-footer-branding.php
	cttel-blocksy-mobile-offcanvas.php
	cttel-blocksy-mobile-header.php
)

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -p "${PORT}")

if [[ -n "${VPS_PASSWORD:-}" ]]; then
  command -v sshpass >/dev/null 2>&1 || { echo "Install sshpass or use SSH key."; exit 1; }
  SSH=(sshpass -p "${VPS_PASSWORD}" ssh "${SSH_OPTS[@]}")
else
  SSH=(ssh "${SSH_OPTS[@]}")
fi

echo "==> Staging sync to ${HOST} (container ${CONTAINER})..."
"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} mkdir -p /var/www/html/wp-content/mu-plugins"

for f in "${MU_FILES[@]}"; do
  src="${ROOT}/mu-plugins/${f}"
  if [[ ! -f "${src}" ]]; then
    echo "Skip missing ${f}"
    continue
  fi
  echo "  ${f}"
  "${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} tee /var/www/html/wp-content/mu-plugins/${f}" < "${src}" >/dev/null
done

TEMPLATE="${ROOT}/mu-plugins/templates/cttel-front-page.php"
if [[ -f "${TEMPLATE}" ]]; then
  echo "  templates/cttel-front-page.php"
  "${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} mkdir -p /var/www/html/wp-content/mu-plugins/templates"
  "${SSH[@]}" "${HOST}" "docker exec -i ${CONTAINER} tee /var/www/html/wp-content/mu-plugins/templates/cttel-front-page.php" < "${TEMPLATE}" >/dev/null
fi

echo "==> Flush caches..."
"${SSH[@]}" "${HOST}" "docker compose -f /root/cursor-mastery/wordpress/docker-compose.yml exec -T wp-init wp cache flush --allow-root 2>/dev/null || docker exec ${CONTAINER} wp cache flush --allow-root 2>/dev/null || true"

echo "Staging homepage mu-plugins synced."
