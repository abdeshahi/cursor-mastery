#!/usr/bin/env bash
# Run on the VPS after deploy. Read-only: does not change n8n or any service.
# Usage: bash /opt/vpn-sales-bot/deploy/verify.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

[[ -f .env ]] || { printf 'ERROR: .env not found in %s\n' "$ROOT" >&2; exit 1; }

# Read a single key from .env without executing the file. Sourcing breaks on
# Persian text with spaces and mangles JSON values.
env_get() {
  sed -n "s/^[[:space:]]*$1=//p" .env \
    | tail -1 \
    | sed -e "s/^'\(.*\)'$/\1/" -e 's/^"\(.*\)"$/\1/'
}

POSTGRES_USER="$(env_get POSTGRES_USER)"; POSTGRES_USER="${POSTGRES_USER:-vpn}"
POSTGRES_DB="$(env_get POSTGRES_DB)"; POSTGRES_DB="${POSTGRES_DB:-vpn_sales}"
HEALTH_HOST="$(env_get HEALTH_HOST)"; HEALTH_HOST="${HEALTH_HOST:-127.0.0.1}"
HEALTH_PORT="$(env_get HEALTH_PORT)"; HEALTH_PORT="${HEALTH_PORT:-3010}"
BOT_TOKEN="$(env_get BOT_TOKEN)"
TELEGRAM_PROXY="$(env_get TELEGRAM_PROXY)"
ADMIN_TELEGRAM_IDS="$(env_get ADMIN_TELEGRAM_IDS)"
MARZBAN_BASE_URL="$(env_get MARZBAN_BASE_URL)"
MARZBAN_USERNAME="$(env_get MARZBAN_USERNAME)"
MARZBAN_PASSWORD="$(env_get MARZBAN_PASSWORD)"
MARZBAN_INSECURE_TLS="$(env_get MARZBAN_INSECURE_TLS)"; MARZBAN_INSECURE_TLS="${MARZBAN_INSECURE_TLS:-false}"
MARZBAN_CURL=(curl -fsS -m 15)
[[ "$MARZBAN_INSECURE_TLS" == true ]] && MARZBAN_CURL+=(-k)

FAILED=0
pass() { printf 'OK   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1" >&2; FAILED=$((FAILED + 1)); }

echo '=== PostgreSQL ==='
if [[ "$(docker inspect --format='{{.State.Health.Status}}' vpn-sales-postgres 2>/dev/null)" == healthy ]]; then
  pass 'container vpn-sales-postgres is healthy'
else
  fail 'container vpn-sales-postgres is not healthy'
  docker ps -a --filter name=vpn-sales-postgres 2>/dev/null || true
fi

if docker exec vpn-sales-postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
  pass 'pg_isready inside container'
else
  fail 'pg_isready failed'
fi

if docker exec vpn-sales-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'SELECT 1' >/dev/null 2>&1; then
  pass "SELECT 1 on $POSTGRES_DB"
else
  fail "SELECT 1 on $POSTGRES_DB failed"
fi

if docker exec vpn-sales-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
    "SELECT to_regclass('public.users') IS NOT NULL" 2>/dev/null | grep -qx t; then
  pass 'users table exists (migrations ran)'
else
  fail 'users table missing — start the bot once so migrations run'
fi

echo '=== Application ==='
if systemctl is-active --quiet vpn-sales-bot; then
  pass 'systemd vpn-sales-bot is active'
else
  fail 'systemd vpn-sales-bot is not active'
fi
if curl -fsS -m 5 "http://${HEALTH_HOST}:${HEALTH_PORT}/health" 2>/dev/null | grep -q '"ok":true'; then
  pass "health endpoint ${HEALTH_HOST}:${HEALTH_PORT}/health"
else
  fail 'health endpoint failed'
fi

echo '=== Telegram ==='
if [[ -z "$BOT_TOKEN" ]]; then
  fail 'BOT_TOKEN missing in .env'
else
  TG_CURL=(curl -fsS -m 15)
  [[ -n "$TELEGRAM_PROXY" ]] && TG_CURL+=(-x "$TELEGRAM_PROXY")
  if "${TG_CURL[@]}" "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null | grep -q '"ok":true'; then
    pass 'Telegram getMe'
  else
    fail 'Telegram getMe failed (token, network, or proxy)'
  fi

  # An admin who never pressed Start cannot receive payment receipts.
  IFS=',' read -r -a ADMIN_LIST <<< "$ADMIN_TELEGRAM_IDS"
  for admin in "${ADMIN_LIST[@]}"; do
    admin="${admin// /}"
    [[ -z "$admin" ]] && continue
    if "${TG_CURL[@]}" -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendChatAction" \
        -d "chat_id=${admin}" -d 'action=typing' 2>/dev/null | grep -q '"ok":true'; then
      pass "admin ${admin} can receive messages"
    else
      fail "admin ${admin} unreachable — open the bot and press Start"
    fi
  done
fi

echo '=== Marzban ==='
if [[ -z "$MARZBAN_BASE_URL" || -z "$MARZBAN_USERNAME" || -z "$MARZBAN_PASSWORD" ]]; then
  fail 'Marzban env vars missing'
else
  TOKEN_JSON="$("${MARZBAN_CURL[@]}" -X POST "${MARZBAN_BASE_URL%/}/api/admin/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=${MARZBAN_USERNAME}" \
    --data-urlencode "password=${MARZBAN_PASSWORD}" \
    --data-urlencode 'grant_type=password' 2>/dev/null || true)"
  TOKEN="$(printf '%s' "$TOKEN_JSON" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
  if [[ -z "$TOKEN" ]]; then
    fail 'Marzban login failed (URL, username, or password)'
  elif "${MARZBAN_CURL[@]}" -H "Authorization: Bearer ${TOKEN}" "${MARZBAN_BASE_URL%/}/api/system" >/dev/null 2>&1; then
    pass 'Marzban /api/system'
  else
    fail 'Marzban /api/system failed'
  fi
fi

echo '=== n8n (existing, read-only check) ==='
if curl -fsS -m 10 http://127.0.0.1:5678/healthz >/dev/null 2>&1; then
  pass 'n8n http://127.0.0.1:5678/healthz'
else
  fail 'n8n healthz failed — do not reinstall; inspect the existing service only'
fi

echo
if [[ "$FAILED" -eq 0 ]]; then
  echo 'All checks passed. Safe to take real payments.'
else
  echo "${FAILED} check(s) failed. Fix them before taking real payments."
  exit 1
fi
