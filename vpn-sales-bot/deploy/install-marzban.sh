#!/usr/bin/env bash
# Install Marzban on the VPS using the official Gozargah installer.
#
# Safe to re-run: if Marzban is already installed it reports and exits
# without touching the existing panel, n8n, or the vpn-sales stack.
#
# Usage (as root on the VPS):
#   bash deploy/install-marzban.sh
# Optional, for HTTPS subscription links on a domain you own:
#   MARZBAN_DOMAIN=panel.example.com bash deploy/install-marzban.sh
set -euo pipefail

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ "${EUID}" -eq 0 ]] || die 'run as root (sudo -i)'

MARZBAN_DIR=/opt/marzban
PANEL_PORT="${MARZBAN_PORT:-8000}"

if ss -lptn 2>/dev/null | grep -q ":${PANEL_PORT} "; then
  if [[ -d "$MARZBAN_DIR" ]]; then
    log "Marzban already listening on ${PANEL_PORT}. Nothing to install."
  else
    die "port ${PANEL_PORT} is already used by something else. Set MARZBAN_PORT to a free port."
  fi
fi

if [[ -d "$MARZBAN_DIR" ]]; then
  log "Marzban is already installed at ${MARZBAN_DIR}. Not reinstalling."
else
  log 'Installing Marzban (official script)'
  bash -c "$(curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh)" @ install
fi

log 'Waiting for the Marzban API'
for _ in $(seq 1 60); do
  if curl -fsS -m 5 "http://127.0.0.1:${PANEL_PORT}/docs" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

PUBLIC_IP="$(curl -4 -fsS -m 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
BASE_URL="http://${PUBLIC_IP}:${PANEL_PORT}"
if [[ -n "${MARZBAN_DOMAIN:-}" ]]; then
  BASE_URL="https://${MARZBAN_DOMAIN}"
fi

# Absolute subscription links. Without this Marzban may return a relative path.
if [[ -f "${MARZBAN_DIR}/.env" ]] && ! grep -q '^XRAY_SUBSCRIPTION_URL_PREFIX' "${MARZBAN_DIR}/.env"; then
  log "Setting XRAY_SUBSCRIPTION_URL_PREFIX=${BASE_URL}"
  printf '\nXRAY_SUBSCRIPTION_URL_PREFIX = %s\n' "$BASE_URL" >> "${MARZBAN_DIR}/.env"
  marzban restart -n || true
fi

cat <<EOF

==> Marzban is up. Two manual steps remain (both need your input):

1) Create the API admin the bot will use:

     marzban cli admin create --sudo

   Pick a username and a strong password. Write them down.

2) Open the dashboard and create at least one inbound (VLESS is fine):

     ${BASE_URL}/dashboard

==> Then put these into /opt/vpn-sales-bot/.env

     MARZBAN_BASE_URL=${BASE_URL}
     MARZBAN_USERNAME=<the admin username from step 1>
     MARZBAN_PASSWORD=<the admin password from step 1>
     MARZBAN_PROXIES={"vless":{}}
     MARZBAN_INBOUNDS={}

   MARZBAN_INBOUNDS={} means "all inbounds for that protocol".
   If you enabled a protocol other than VLESS, change MARZBAN_PROXIES to match.

==> Verify before selling:

     bash /opt/vpn-sales-bot/deploy/verify.sh

EOF
