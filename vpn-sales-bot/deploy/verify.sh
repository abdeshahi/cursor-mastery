#!/usr/bin/env bash
# Run on the VPS after deploy. Does not change n8n.
# Usage: cd /opt/vpn-sales-bot && bash deploy/verify.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

pass() { printf 'OK   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1" >&2; }

echo '=== PostgreSQL ==='
if docker inspect --format='{{.State.Health.Status}}' vpn-sales-postgres 2>/dev/null | grep -qx healthy; then
  pass 'container vpn-sales-postgres is healthy'
else
  fail 'container vpn-sales-postgres is not healthy'
  docker ps -a --filter name=vpn-sales-postgres || true
fi

if docker exec vpn-sales-postgres pg_isready -U "${POSTGRES_USER:-vpn}" -d "${POSTGRES_DB:-vpn_sales}" >/dev/null; then
  pass 'pg_isready inside container'
else
  fail 'pg_isready failed'
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
  if docker exec vpn-sales-postgres psql -U "${POSTGRES_USER:-vpn}" -d "${POSTGRES_DB:-vpn_sales}" -c 'SELECT 1' >/dev/null; then
    pass 'SELECT 1 on vpn_sales'
  else
    fail 'SELECT 1 on vpn_sales failed'
  fi
  if docker exec vpn-sales-postgres psql -U "${POSTGRES_USER:-vpn}" -d "${POSTGRES_DB:-vpn_sales}" -c '\dt' | grep -q users; then
    pass 'users table exists (migrations ran)'
  else
    fail 'users table missing — start the bot once so migrations run'
  fi
fi

echo '=== Application ==='
if systemctl is-active --quiet vpn-sales-bot; then
  pass 'systemd vpn-sales-bot is active'
else
  fail 'systemd vpn-sales-bot is not active'
fi
if curl -fsS -m 5 "http://${HEALTH_HOST:-127.0.0.1}:${HEALTH_PORT:-3010}/health" | grep -q '"ok":true'; then
  pass "health endpoint ${HEALTH_HOST:-127.0.0.1}:${HEALTH_PORT:-3010}/health"
else
  fail 'health endpoint failed'
fi

echo '=== Telegram ==='
if [[ -z "${BOT_TOKEN:-}" ]]; then
  fail 'BOT_TOKEN missing in .env'
else
  TG_CURL=(curl -fsS -m 15)
  if [[ -n "${TELEGRAM_PROXY:-}" ]]; then
    TG_CURL+=(-x "$TELEGRAM_PROXY")
  fi
  if "${TG_CURL[@]}" "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
    pass 'Telegram getMe'
  else
    fail 'Telegram getMe failed (token, network, or proxy)'
  fi
fi

echo '=== Marzban ==='
if [[ -z "${MARZBAN_BASE_URL:-}" || -z "${MARZBAN_USERNAME:-}" || -z "${MARZBAN_PASSWORD:-}" ]]; then
  fail 'Marzban env vars missing'
else
  TOKEN_JSON="$(curl -fsS -m 15 -X POST "${MARZBAN_BASE_URL%/}/api/admin/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=${MARZBAN_USERNAME}" \
    --data-urlencode "password=${MARZBAN_PASSWORD}" \
    --data-urlencode 'grant_type=password' || true)"
  TOKEN="$(printf '%s' "$TOKEN_JSON" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
  if [[ -n "$TOKEN" ]] && curl -fsS -m 15 -H "Authorization: Bearer ${TOKEN}" "${MARZBAN_BASE_URL%/}/api/system" >/dev/null; then
    pass 'Marzban /api/system'
  else
    fail 'Marzban login or /api/system failed'
  fi
fi

echo '=== n8n (existing, read-only check) ==='
if curl -fsS -m 10 http://127.0.0.1:5678/healthz >/dev/null; then
  pass 'n8n http://127.0.0.1:5678/healthz'
else
  fail 'n8n healthz failed — do not reinstall; inspect the existing service only'
fi

echo
echo 'Done. Fix any FAIL lines before taking real payments.'
