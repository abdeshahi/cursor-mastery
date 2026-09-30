#!/usr/bin/env bash
# Expose Marzban subscription links over plain HTTP on port 8090.
# Safe to re-run. Does not touch n8n or the bot service.
#
# Usage (as root on the VPS):
#   bash /opt/vpn-sales-bot/deploy/install-subscription-proxy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXY_PORT="${SUBSCRIPTION_PROXY_PORT:-8090}"
MARZBAN_DIR="${MARZBAN_DIR:-/opt/marzban}"
BOT_ENV_FILE="${BOT_ENV_FILE:-/opt/vpn-sales-bot/.env}"
NGINX_SITE="/etc/nginx/sites-available/vpn-sales-subscription-proxy"
NGINX_LINK="/etc/nginx/sites-enabled/vpn-sales-subscription-proxy"

log() { printf '\n==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ "${EUID}" -eq 0 ]] || die 'run as root'

PUBLIC_IP="$(hostname -I | awk '{print $1}')"
[[ -n "$PUBLIC_IP" ]] || die 'could not determine public IP'
SUB_PREFIX="http://${PUBLIC_IP}:${PROXY_PORT}"

if ! command -v nginx >/dev/null 2>&1; then
  log 'Installing nginx'
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nginx
fi

if ss -lptn 2>/dev/null | grep -q ":${PROXY_PORT} " && ! grep -q 'vpn-sales-subscription-proxy' "$NGINX_SITE" 2>/dev/null; then
  die "port ${PROXY_PORT} is already in use by another service"
fi

log "Installing nginx site on port ${PROXY_PORT}"
install -m 644 "${ROOT}/deploy/nginx-subscription-proxy.conf" "$NGINX_SITE"
sed -i "s/listen 8090;/listen ${PROXY_PORT};/" "$NGINX_SITE"
sed -i "s/listen \\[::\\]:8090;/listen [::]:${PROXY_PORT};/" "$NGINX_SITE"
ln -sf "$NGINX_SITE" "$NGINX_LINK"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx >/dev/null 2>&1 || true
systemctl reload nginx

if [[ -f "${MARZBAN_DIR}/.env" ]]; then
  log "Setting XRAY_SUBSCRIPTION_URL_PREFIX=${SUB_PREFIX}"
  python3 - "$MARZBAN_DIR/.env" "$SUB_PREFIX" <<'PY'
import re
import sys

path, prefix = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as handle:
    text = handle.read()
text = re.sub(r"^[ \t]*XRAY_SUBSCRIPTION_URL_PREFIX[ \t]*=.*\n", "", text, flags=re.M)
text = text.rstrip() + f'\nXRAY_SUBSCRIPTION_URL_PREFIX = "{prefix}"\n'
with open(path, "w", encoding="utf-8") as handle:
    handle.write(text)
PY
  marzban restart -n >/dev/null 2>&1 || warn 'marzban restart failed — restart manually: marzban restart'
fi

if [[ -f "$BOT_ENV_FILE" ]]; then
  log "Setting MARZBAN_SUBSCRIPTION_URL_PREFIX in ${BOT_ENV_FILE}"
  python3 - "$BOT_ENV_FILE" "$SUB_PREFIX" <<'PY'
import re
import sys

path, prefix = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as handle:
    text = handle.read()
line = f"MARZBAN_SUBSCRIPTION_URL_PREFIX={prefix}"
if re.search(r"^[ \t]*MARZBAN_SUBSCRIPTION_URL_PREFIX[ \t]*=", text, re.M):
    text = re.sub(r"^[ \t]*MARZBAN_SUBSCRIPTION_URL_PREFIX[ \t]*=.*$", line, text, flags=re.M)
else:
    text = text.rstrip() + "\n" + line + "\n"
with open(path, "w", encoding="utf-8") as handle:
    handle.write(text)
PY
fi

log 'Smoke test: HTTP subscription fetch'
TOKEN_PATH="$(curl -fsS -m 10 "http://127.0.0.1:${PROXY_PORT}/sub/" 2>/dev/null || true)"
# Need a real token — grab one user if bot env + marzban are configured
if [[ -f "$BOT_ENV_FILE" ]]; then
  MARZBAN_USER="$(sed -n 's/^ *MARZBAN_USERNAME *= *//p' "$BOT_ENV_FILE" | tail -1 | tr -d "\"'")"
  MARZBAN_PASS="$(sed -n 's/^ *MARZBAN_PASSWORD *= *//p' "$BOT_ENV_FILE" | tail -1 | tr -d "\"'")"
  if [[ -n "$MARZBAN_USER" && -n "$MARZBAN_PASS" ]]; then
    API_TOKEN="$(curl -fsSk -m 15 -X POST "https://127.0.0.1:8000/api/admin/token" \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      --data-urlencode "username=${MARZBAN_USER}" \
      --data-urlencode "password=${MARZBAN_PASS}" \
      --data-urlencode 'grant_type=password' 2>/dev/null \
      | python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null || true)"
    if [[ -n "$API_TOKEN" ]]; then
      SUB="$(curl -fsSk -m 15 -H "Authorization: Bearer ${API_TOKEN}" \
        "https://127.0.0.1:8000/api/user/ct_1" 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("subscription_url",""))' 2>/dev/null || true)"
      SUB="${SUB#https://*8000}"
      SUB="${SUB#http://*8090}"
      if [[ -n "$SUB" ]]; then
        BODY="$(curl -fsS -m 10 "http://127.0.0.1:${PROXY_PORT}${SUB}" 2>/dev/null | head -c 200 || true)"
        [[ -n "$BODY" ]] || die "subscription proxy returned empty body for ${SUB}"
        log "Subscription proxy OK (${#BODY} bytes fetched)"
      fi
    fi
  fi
fi

cat <<EOF

Subscription proxy ready:
  Public prefix : ${SUB_PREFIX}
  nginx site    : ${NGINX_SITE}

Restart the bot so new orders use the HTTP subscription prefix:
  systemctl restart vpn-sales-bot
EOF
