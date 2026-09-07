#!/usr/bin/env bash
# Install and fully configure Marzban on the VPS, non-interactively.
#
# Does everything the bot needs to start selling:
#   1. installs Marzban (official Gozargah installer) if missing
#   2. sets XRAY_SUBSCRIPTION_URL_PREFIX so subscription links are absolute
#   3. creates a sudo API admin for the bot
#   4. adds a VLESS + Reality inbound if the panel has no usable inbound
#   5. proves it works by creating and deleting a throwaway API user
#   6. writes MARZBAN_* into /opt/vpn-sales-bot/.env
#
# Safe to re-run: existing panel, admins, inbounds, n8n and the vpn-sales
# stack are left alone. Nothing is deleted.
#
# Usage (as root on the VPS):
#   bash deploy/install-marzban.sh
#
# Optional overrides:
#   MARZBAN_DOMAIN=panel.example.com    # HTTPS base URL instead of http://IP
#   MARZBAN_PORT=8000                   # panel port
#   MARZBAN_ADMIN_USERNAME=vpnsalesbot  # API admin the bot logs in as
#   MARZBAN_ADMIN_PASSWORD=...          # generated when omitted
#   REALITY_SNI=www.datadoghq.com       # Reality camouflage domain
#   XRAY_PORT=443                       # Reality listen port
#   BOT_ENV_FILE=/opt/vpn-sales-bot/.env
set -euo pipefail

log() { printf '\n==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

[[ "${EUID}" -eq 0 ]] || die 'run as root (sudo -i)'

MARZBAN_DIR=/opt/marzban
XRAY_CONFIG=/var/lib/marzban/xray_config.json
PANEL_PORT="${MARZBAN_PORT:-8000}"
ADMIN_USER="${MARZBAN_ADMIN_USERNAME:-vpnsalesbot}"
REALITY_SNI="${REALITY_SNI:-www.datadoghq.com}"
BOT_ENV_FILE="${BOT_ENV_FILE:-/opt/vpn-sales-bot/.env}"

for tool in curl python3; do
  command -v "$tool" >/dev/null 2>&1 || die "$tool is required. Install it: apt-get install -y $tool"
done

# ---------------------------------------------------------------- install ----

if [[ -d "$MARZBAN_DIR" ]]; then
  log "Marzban already installed at ${MARZBAN_DIR}. Not reinstalling."
elif ss -lptn 2>/dev/null | grep -q ":${PANEL_PORT} "; then
  die "port ${PANEL_PORT} is already in use by something else. Set MARZBAN_PORT to a free port."
else
  log 'Installing Marzban (official script)'
  bash -c "$(curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh)" @ install
fi

command -v marzban >/dev/null 2>&1 || die 'the marzban CLI is missing; the installer did not finish'

wait_for_api() {
  for _ in $(seq 1 90); do
    if curl -fsS -m 5 "http://127.0.0.1:${PANEL_PORT}/docs" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

log 'Waiting for the Marzban API'
wait_for_api || die "Marzban API never came up on port ${PANEL_PORT}. Check: marzban logs"

# ---------------------------------------------------------------- base url ----

PUBLIC_IP="$(curl -4 -fsS -m 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
[[ -n "$PUBLIC_IP" ]] || die 'could not determine the public IP of this VPS'

if [[ -n "${MARZBAN_DOMAIN:-}" ]]; then
  BASE_URL="https://${MARZBAN_DOMAIN}"
else
  BASE_URL="http://${PUBLIC_IP}:${PANEL_PORT}"
fi

# Without this Marzban hands out relative subscription paths, which are
# useless inside a Telegram message.
if [[ -f "${MARZBAN_DIR}/.env" ]] && ! grep -q '^ *XRAY_SUBSCRIPTION_URL_PREFIX' "${MARZBAN_DIR}/.env"; then
  log "Setting XRAY_SUBSCRIPTION_URL_PREFIX=${BASE_URL}"
  printf '\nXRAY_SUBSCRIPTION_URL_PREFIX = "%s"\n' "$BASE_URL" >>"${MARZBAN_DIR}/.env"
  marzban restart -n >/dev/null 2>&1 || true
  wait_for_api || die 'Marzban did not come back after restart. Check: marzban logs'
fi

# ------------------------------------------------------------------ admin ----

api_token() {
  curl -fsS -m 10 -X POST "http://127.0.0.1:${PANEL_PORT}/api/admin/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=${1}" \
    --data-urlencode "password=${2}" \
    --data-urlencode 'grant_type=password' 2>/dev/null |
    python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null
}

ADMIN_PASS="${MARZBAN_ADMIN_PASSWORD:-}"
TOKEN=''

if [[ -n "$ADMIN_PASS" ]]; then
  TOKEN="$(api_token "$ADMIN_USER" "$ADMIN_PASS")"
fi

if [[ -z "$TOKEN" ]] && [[ -f "$BOT_ENV_FILE" ]]; then
  # Reuse the credentials already deployed, so re-runs stay idempotent.
  EXISTING_USER="$(sed -n 's/^ *MARZBAN_USERNAME *= *//p' "$BOT_ENV_FILE" | tail -1 | tr -d "\"'")"
  EXISTING_PASS="$(sed -n 's/^ *MARZBAN_PASSWORD *= *//p' "$BOT_ENV_FILE" | tail -1 | tr -d "\"'")"
  if [[ -n "$EXISTING_USER" && -n "$EXISTING_PASS" ]]; then
    TOKEN="$(api_token "$EXISTING_USER" "$EXISTING_PASS")"
    if [[ -n "$TOKEN" ]]; then
      log "Reusing the existing API admin '${EXISTING_USER}' from ${BOT_ENV_FILE}"
      ADMIN_USER="$EXISTING_USER"
      ADMIN_PASS="$EXISTING_PASS"
    fi
  fi
fi

if [[ -z "$TOKEN" ]]; then
  # A username collision means we cannot recover the old password, so take a
  # fresh name rather than touching an admin someone else may be using.
  if marzban cli admin list 2>/dev/null | grep -qw "$ADMIN_USER"; then
    ADMIN_USER="${ADMIN_USER}$(date +%s | tail -c 5)"
    log "That admin name was taken. Using '${ADMIN_USER}' instead."
  fi

  ADMIN_PASS="${MARZBAN_ADMIN_PASSWORD:-$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)}"

  log "Creating sudo API admin '${ADMIN_USER}'"
  # Flag names differ between Marzban releases, so fall back to the prompts.
  marzban cli admin create --username "$ADMIN_USER" --password "$ADMIN_PASS" --sudo >/dev/null 2>&1 ||
    printf '%s\ny\n%s\n%s\n' "$ADMIN_USER" "$ADMIN_PASS" "$ADMIN_PASS" |
    marzban cli admin create --sudo >/dev/null 2>&1 || true

  TOKEN="$(api_token "$ADMIN_USER" "$ADMIN_PASS")"
  [[ -n "$TOKEN" ]] || die "could not create or log in as an API admin. Create one by hand: marzban cli admin create --sudo"
fi

log 'API admin authenticated'

# --------------------------------------------------------------- inbounds ----

api_get() {
  curl -fsS -m 10 -H "Authorization: Bearer ${TOKEN}" "http://127.0.0.1:${PANEL_PORT}${1}"
}

# Marzban returns {"vless": [{"tag": ...}], "vmess": [...]}. Any protocol with
# at least one inbound is enough for the bot.
first_protocol_with_inbound() {
  api_get /api/inbounds 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for proto in ("vless", "vmess", "trojan", "shadowsocks"):
    if data.get(proto):
        print(proto)
        break
' 2>/dev/null
}

PROTOCOL="$(first_protocol_with_inbound)"

if [[ -n "$PROTOCOL" ]]; then
  log "Panel already has a usable '${PROTOCOL}' inbound. Leaving the Xray config alone."
else
  log 'No usable inbound found. Adding VLESS + Reality.'
  [[ -f "$XRAY_CONFIG" ]] || die "expected the Xray config at ${XRAY_CONFIG} but it is missing"

  XRAY_PORT="${XRAY_PORT:-443}"
  if ss -lptn 2>/dev/null | grep -q ":${XRAY_PORT} "; then
    XRAY_PORT=8443
    warn "port 443 is busy, using ${XRAY_PORT} for Reality instead"
  fi

  MARZBAN_CONTAINER="$(docker ps --filter 'name=marzban' --format '{{.Names}}' 2>/dev/null | grep -v node | head -1)"
  [[ -n "$MARZBAN_CONTAINER" ]] || die 'the Marzban container is not running. Check: marzban logs'

  KEYS="$(docker exec "$MARZBAN_CONTAINER" xray x25519 2>/dev/null)"
  # Xray renamed these labels across versions (Private key / PrivateKey, Public key / Password).
  REALITY_PRIVATE="$(printf '%s' "$KEYS" | grep -iE 'private' | head -1 | awk '{print $NF}')"
  [[ -n "$REALITY_PRIVATE" ]] || die 'could not generate a Reality keypair with xray x25519'
  SHORT_ID="$(head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n')"

  cp -a "$XRAY_CONFIG" "${XRAY_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

  XRAY_CONFIG="$XRAY_CONFIG" \
  XRAY_PORT="$XRAY_PORT" \
  REALITY_SNI="$REALITY_SNI" \
  REALITY_PRIVATE="$REALITY_PRIVATE" \
  SHORT_ID="$SHORT_ID" \
    python3 <<'PY'
import json, os

path = os.environ["XRAY_CONFIG"]
port = int(os.environ["XRAY_PORT"])
sni = os.environ["REALITY_SNI"]

with open(path, encoding="utf-8") as handle:
    config = json.load(handle)

inbounds = config.setdefault("inbounds", [])
tag = "VLESS TCP REALITY"
inbounds = [item for item in inbounds if item.get("tag") != tag]

inbounds.append(
    {
        "tag": tag,
        "listen": "0.0.0.0",
        "port": port,
        "protocol": "vless",
        # Marzban injects per-user clients itself; this list must stay empty.
        "settings": {"clients": [], "decryption": "none"},
        "streamSettings": {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "show": False,
                "dest": f"{sni}:443",
                "xver": 0,
                "serverNames": [sni],
                "privateKey": os.environ["REALITY_PRIVATE"],
                "shortIds": [os.environ["SHORT_ID"]],
            },
        },
        "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
    }
)
config["inbounds"] = inbounds

with open(path, "w", encoding="utf-8") as handle:
    json.dump(config, handle, indent=2, ensure_ascii=False)
PY

  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
    ufw allow "${XRAY_PORT}/tcp" >/dev/null 2>&1 || warn "could not open ${XRAY_PORT}/tcp in ufw"
    ufw allow "${PANEL_PORT}/tcp" >/dev/null 2>&1 || warn "could not open ${PANEL_PORT}/tcp in ufw"
  fi

  log "Restarting Marzban with the new inbound on port ${XRAY_PORT}"
  marzban restart -n >/dev/null 2>&1 || true
  wait_for_api || die 'Marzban did not come back after restart. Check: marzban logs'

  TOKEN="$(api_token "$ADMIN_USER" "$ADMIN_PASS")"
  PROTOCOL="$(first_protocol_with_inbound)"
  [[ -n "$PROTOCOL" ]] || die "the inbound did not register. Inspect ${XRAY_CONFIG} and run: marzban logs"
fi

# ------------------------------------------------------------ smoke test ----

log 'Smoke test: creating a throwaway API user'
PROBE_USER="probe$(date +%s)"

PROBE_RESULT="$(
  curl -fsS -m 15 -X POST "http://127.0.0.1:${PANEL_PORT}/api/user" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${PROBE_USER}\",\"expire\":$(($(date +%s) + 3600)),\"data_limit\":1073741824,\"data_limit_reset_strategy\":\"no_reset\",\"status\":\"active\",\"note\":\"install-marzban.sh smoke test\",\"proxies\":{\"${PROTOCOL}\":{}},\"inbounds\":{}}" 2>&1
)" || die "the API rejected user creation. Response: ${PROBE_RESULT}"

SUB_URL="$(printf '%s' "$PROBE_RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("subscription_url",""))' 2>/dev/null)"

curl -fsS -m 10 -X DELETE "http://127.0.0.1:${PANEL_PORT}/api/user/${PROBE_USER}" \
  -H "Authorization: Bearer ${TOKEN}" >/dev/null 2>&1 ||
  warn "could not delete the probe user '${PROBE_USER}'. Remove it from the dashboard."

[[ -n "$SUB_URL" ]] || die 'the API returned no subscription_url'
if [[ "$SUB_URL" != http* ]]; then
  warn "subscription_url is relative ('${SUB_URL}'). The bot will prefix it with MARZBAN_SUBSCRIPTION_URL_PREFIX."
fi
log "Smoke test passed. Subscription URL looks like: ${SUB_URL}"

# --------------------------------------------------------------- bot .env ----

MARZBAN_PROXIES="{\"${PROTOCOL}\":{}}"

if [[ -f "$BOT_ENV_FILE" ]]; then
  log "Writing MARZBAN_* into ${BOT_ENV_FILE}"
  cp -a "$BOT_ENV_FILE" "${BOT_ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"

  python3 - "$BOT_ENV_FILE" \
    "MARZBAN_BASE_URL=${BASE_URL}" \
    "MARZBAN_USERNAME=${ADMIN_USER}" \
    "MARZBAN_PASSWORD=${ADMIN_PASS}" \
    "MARZBAN_PROXIES='${MARZBAN_PROXIES}'" \
    "MARZBAN_INBOUNDS='{}'" <<'PY'
import re
import sys

path, pairs = sys.argv[1], sys.argv[2:]
with open(path, encoding="utf-8") as handle:
    text = handle.read()

for pair in pairs:
    key, value = pair.split("=", 1)
    line = f"{key}={value}"
    active = re.compile(rf"^[ \t]*{re.escape(key)}[ \t]*=.*$", re.MULTILINE)
    commented = re.compile(rf"^[ \t]*#[ \t]*{re.escape(key)}[ \t]*=.*$", re.MULTILINE)
    # An active assignment wins over a commented example of the same key.
    for pattern in (active, commented):
        if pattern.search(text):
            text = pattern.sub(line, text, count=1)
            break
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"

with open(path, "w", encoding="utf-8") as handle:
    handle.write(text)
PY
  chmod 600 "$BOT_ENV_FILE"
  ENV_NOTE="Already written to ${BOT_ENV_FILE} (a timestamped backup was kept)."
else
  ENV_NOTE="${BOT_ENV_FILE} does not exist yet. Copy the block below into it."
fi

cat <<EOF

============================================================
Marzban is configured and verified.

  Panel dashboard : ${BASE_URL}/dashboard
  API admin       : ${ADMIN_USER}
  API password    : ${ADMIN_PASS}
  Active protocol : ${PROTOCOL}

${ENV_NOTE}

MARZBAN_BASE_URL=${BASE_URL}
MARZBAN_USERNAME=${ADMIN_USER}
MARZBAN_PASSWORD=${ADMIN_PASS}
MARZBAN_PROXIES='${MARZBAN_PROXIES}'
MARZBAN_INBOUNDS='{}'

MARZBAN_INBOUNDS='{}' means "every inbound of that protocol".

Next:
  systemctl restart vpn-sales-bot
  bash /opt/vpn-sales-bot/deploy/verify.sh
============================================================

EOF
