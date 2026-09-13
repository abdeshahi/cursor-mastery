#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  echo "Missing .env — run scripts/generate-env.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .env

if [[ "${DOMAIN}" == "example.com" ]] || [[ -z "${DOMAIN}" ]]; then
  echo "Set a real DOMAIN in .env before requesting Let's Encrypt certificate."
  exit 1
fi

if [[ -z "${LETSENCRYPT_EMAIL:-}" ]]; then
  echo "Set LETSENCRYPT_EMAIL in .env."
  exit 1
fi

echo "Requesting certificate for ${DOMAIN}..."
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "${LETSENCRYPT_EMAIL}" \
  --agree-tos \
  --no-eff-email \
  -d "${DOMAIN}"

"${ROOT_DIR}/scripts/enable-ssl.sh"

echo "SSL setup complete."
