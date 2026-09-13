#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

"${ROOT_DIR}/scripts/generate-env.sh"

PUBLIC_IP="$(curl -4 -fsS --max-time 5 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"
if grep -q '^DOMAIN=example.com' "${ROOT_DIR}/.env"; then
  sed -i "s/^DOMAIN=.*/DOMAIN=${PUBLIC_IP}/" "${ROOT_DIR}/.env"
  echo "DOMAIN set to server IP: ${PUBLIC_IP} (update .env when you have a real domain)"
fi
if grep -q '^DOMAIN=cttel\.ir' "${ROOT_DIR}/.env"; then
  echo "DOMAIN is cttel.ir — ensure DNS A record points to ${PUBLIC_IP} before SSL."
fi

echo "Starting WordPress stack..."
docker compose up -d db wordpress nginx

echo "Waiting for database..."
sleep 15

echo "Running WordPress initialization (fa_IR + WooCommerce)..."
docker compose run --rm wp-init

"${ROOT_DIR}/scripts/write-credentials.sh"

echo ""
echo "Deployment complete."
echo "  HTTP:  http://${PUBLIC_IP}"
echo "  Admin: http://${PUBLIC_IP}/wp-admin"
echo ""
echo "Next steps:"
echo "  1. Point your domain DNS A record to ${PUBLIC_IP}"
echo "  2. Update DOMAIN and LETSENCRYPT_EMAIL in .env"
echo "  3. Run: ./scripts/init-ssl.sh"
echo "  4. Run: sudo ./scripts/setup-firewall.sh"
echo "  5. Run: ./scripts/install-cron-backup.sh"
