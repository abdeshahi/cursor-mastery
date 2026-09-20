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

SSL_CONF="${ROOT_DIR}/nginx/conf.d/01-ssl.conf"
SSL_TEMPLATE="${ROOT_DIR}/nginx/conf.d/01-ssl.conf.template"
HTTP_CONF="${ROOT_DIR}/nginx/conf.d/00-http.conf"
HTTP_SSL_REDIRECT="${ROOT_DIR}/nginx/conf.d/00-http-redirect.conf"

if [[ ! -f "certbot/conf/live/${DOMAIN}/fullchain.pem" ]]; then
  echo "Certificate not found for ${DOMAIN}."
  exit 1
fi

export DOMAIN
envsubst '${DOMAIN}' < "${SSL_TEMPLATE}" > "${SSL_CONF}"

cat > "${HTTP_SSL_REDIRECT}" <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
        default_type "text/plain";
        try_files $uri =404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
EOF

mv "${HTTP_CONF}" "${HTTP_CONF}.bak" 2>/dev/null || true

docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload

echo "HTTPS enabled for ${DOMAIN}."
