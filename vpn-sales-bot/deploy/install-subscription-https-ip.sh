#!/usr/bin/env bash
# Serve Marzban subscriptions over trusted HTTPS on an IP address without
# touching the Xray/REALITY listener on port 443.
#
# Let's Encrypt IP certificates are short-lived (160 hours). Certbot's timer
# and the deploy hook below are therefore required, not optional.
#
# Usage:
#   bash /opt/vpn-sales-bot/deploy/install-subscription-https-ip.sh
#
# Optional:
#   PUBLIC_IP=203.0.113.10 HTTPS_PORT=8443 LETSENCRYPT_EMAIL=ops@example.com bash ...
set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-$(hostname -I | awk '{print $1}')}"
HTTPS_PORT="${HTTPS_PORT:-8443}"
WEBROOT="${ACME_WEBROOT:-/var/www/vpn-sales-acme}"
CERT_NAME="${CERT_NAME:-vpn-sales-sub-ip}"
BOT_ENV_FILE="${BOT_ENV_FILE:-/opt/vpn-sales-bot/.env}"
CHALLENGE_SITE="/etc/nginx/sites-available/vpn-sales-acme"
HTTPS_SITE="/etc/nginx/sites-available/vpn-sales-subscription-https"
CERTBOT_BIN="/snap/bin/certbot"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ "${EUID}" -eq 0 ]] || die 'run as root'
[[ "${PUBLIC_IP}" =~ ^[0-9a-fA-F:.]+$ ]] || die 'PUBLIC_IP is invalid'
[[ "${HTTPS_PORT}" =~ ^[0-9]+$ ]] || die 'HTTPS_PORT must be numeric'
(( HTTPS_PORT >= 1 && HTTPS_PORT <= 65535 )) || die 'HTTPS_PORT is out of range'
[[ "${HTTPS_PORT}" != "443" ]] || die 'port 443 is reserved for the production REALITY listener'
command -v nginx >/dev/null 2>&1 || die 'nginx is required'

if [[ ! -x "${CERTBOT_BIN}" ]]; then
  log 'Installing current Certbot from the official snap'
  snap install certbot --classic
fi

CERTBOT_VERSION="$("${CERTBOT_BIN}" --version 2>&1 | awk '{print $2}')"
python3 - "${CERTBOT_VERSION}" <<'PY'
import sys
parts = tuple(int(part) for part in sys.argv[1].split(".")[:2])
if parts < (5, 4):
    raise SystemExit("Certbot 5.4 or newer is required for webroot IP certificates")
PY

install -d -m 0755 "${WEBROOT}/.well-known/acme-challenge"

cat >"${CHALLENGE_SITE}" <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location /.well-known/acme-challenge/ {
        root ${WEBROOT};
        default_type text/plain;
    }

    location / {
        return 404;
    }
}
EOF
ln -sfn "${CHALLENGE_SITE}" /etc/nginx/sites-enabled/vpn-sales-acme
nginx -t
systemctl reload nginx

CERTBOT_CONTACT=(--register-unsafely-without-email)
if [[ -n "${LETSENCRYPT_EMAIL:-}" ]]; then
  CERTBOT_CONTACT=(--email "${LETSENCRYPT_EMAIL}")
fi

CERT_PATH="/etc/letsencrypt/live/${CERT_NAME}/fullchain.pem"
if [[ ! -s "${CERT_PATH}" ]]; then
  log 'Validating IP ownership against Let’s Encrypt staging'
  "${CERTBOT_BIN}" certonly \
    --staging \
    --non-interactive \
    --agree-tos \
    "${CERTBOT_CONTACT[@]}" \
    --preferred-profile shortlived \
    --webroot \
    --webroot-path "${WEBROOT}" \
    --ip-address "${PUBLIC_IP}" \
    --cert-name "${CERT_NAME}-staging"
  "${CERTBOT_BIN}" delete --non-interactive --cert-name "${CERT_NAME}-staging"

  log 'Requesting trusted short-lived IP certificate'
  "${CERTBOT_BIN}" certonly \
    --non-interactive \
    --agree-tos \
    "${CERTBOT_CONTACT[@]}" \
    --preferred-profile shortlived \
    --webroot \
    --webroot-path "${WEBROOT}" \
    --ip-address "${PUBLIC_IP}" \
    --cert-name "${CERT_NAME}"
fi

[[ -s "${CERT_PATH}" ]] || die "certificate was not created at ${CERT_PATH}"

cat >"${HTTPS_SITE}" <<EOF
server {
    listen ${HTTPS_PORT} ssl;
    listen [::]:${HTTPS_PORT} ssl;
    server_name ${PUBLIC_IP};

    ssl_certificate /etc/letsencrypt/live/${CERT_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${CERT_NAME}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:VPNSubTLS:10m;
    ssl_session_timeout 10m;

    location /sub/ {
        proxy_pass https://127.0.0.1:8000/sub/;
        proxy_ssl_verify off;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        add_header Cache-Control "no-store" always;
    }

    location / {
        return 404;
    }
}
EOF
ln -sfn "${HTTPS_SITE}" /etc/nginx/sites-enabled/vpn-sales-subscription-https

install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
cat >/etc/letsencrypt/renewal-hooks/deploy/reload-vpn-sales-nginx <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
nginx -t
systemctl reload nginx
EOF
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/reload-vpn-sales-nginx

nginx -t
systemctl reload nginx
systemctl enable --now snap.certbot.renew.timer >/dev/null

SUB_PREFIX="https://${PUBLIC_IP}:${HTTPS_PORT}"
if [[ -f "${BOT_ENV_FILE}" ]]; then
  python3 - "${BOT_ENV_FILE}" "${SUB_PREFIX}" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
prefix = sys.argv[2]
text = path.read_text(encoding="utf-8")
line = f"MARZBAN_SUBSCRIPTION_URL_PREFIX={prefix}"
if re.search(r"^[ \t]*MARZBAN_SUBSCRIPTION_URL_PREFIX[ \t]*=", text, re.M):
    text = re.sub(r"^[ \t]*MARZBAN_SUBSCRIPTION_URL_PREFIX[ \t]*=.*$", line, text, flags=re.M)
else:
    text = text.rstrip() + "\n" + line + "\n"
path.write_text(text, encoding="utf-8")
path.chmod(0o600)
PY
fi

log "Trusted subscription endpoint ready at ${SUB_PREFIX}/sub/{token}"
log 'The HTTP :8090 compatibility endpoint was intentionally left in place'
