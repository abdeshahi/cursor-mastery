#!/usr/bin/env bash
# Tune VLESS+Reality for Iranian mobile ISPs (MCI/Hamrah Aval, Irancell, …).
# Port 443 to a direct VPS IP is often blocked; a high port + whitelisted SNI works better.
#
# Usage (as root on the VPS):
#   REALITY_PORT=8443 REALITY_SNI=www.microsoft.com bash deploy/fix-reality-mobile-iran.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
XRAY_CONFIG="${XRAY_CONFIG:-/var/lib/marzban/xray_config.json}"
BOT_ENV_FILE="${BOT_ENV_FILE:-/opt/vpn-sales-bot/.env}"
REALITY_PORT="${REALITY_PORT:-8443}"
REALITY_SNI="${REALITY_SNI:-www.microsoft.com}"
INBOUND_TAG="${INBOUND_TAG:-VLESS TCP REALITY}"
PUBLIC_IP="$(hostname -I | awk '{print $1}')"

log() { printf '\n==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ "${EUID}" -eq 0 ]] || die 'run as root'
[[ -f "$XRAY_CONFIG" ]] || die "missing ${XRAY_CONFIG}"
[[ -n "$PUBLIC_IP" ]] || die 'could not determine public IP'

log "Updating Reality inbound → port ${REALITY_PORT}, SNI ${REALITY_SNI}"
cp -a "$XRAY_CONFIG" "${XRAY_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

XRAY_CONFIG="$XRAY_CONFIG" REALITY_PORT="$REALITY_PORT" REALITY_SNI="$REALITY_SNI" INBOUND_TAG="$INBOUND_TAG" \
  python3 <<'PY'
import json
import os

path = os.environ["XRAY_CONFIG"]
port = int(os.environ["REALITY_PORT"])
sni = os.environ["REALITY_SNI"]
tag = os.environ["INBOUND_TAG"]

with open(path, encoding="utf-8") as handle:
    config = json.load(handle)

found = False
for inbound in config.get("inbounds", []):
    if inbound.get("tag") != tag:
        continue
    found = True
    inbound["port"] = port
    reality = inbound.setdefault("streamSettings", {}).setdefault("realitySettings", {})
    reality["dest"] = f"{sni}:443"
    reality["serverNames"] = [sni]
    break

if not found:
    raise SystemExit(f"inbound tag not found: {tag}")

with open(path, "w", encoding="utf-8") as handle:
    json.dump(config, handle, indent=2, ensure_ascii=False)
PY

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
  ufw allow "${REALITY_PORT}/tcp" >/dev/null 2>&1 || warn "could not open ${REALITY_PORT}/tcp in ufw"
fi

log 'Restarting Marzban'
marzban restart -n >/dev/null 2>&1 || die 'marzban restart failed'

API_READY=false
for _ in $(seq 1 45); do
  if curl -fsSk -m 5 "https://127.0.0.1:8000/openapi.json" >/dev/null 2>&1; then
    API_READY=true
    break
  fi
  sleep 2
done
[[ "$API_READY" == true ]] || die 'Marzban API did not come back'

log 'Updating host settings and enabling xtls-rprx-vision flow for users'
python3 - "$BOT_ENV_FILE" "$PUBLIC_IP" "$REALITY_PORT" "$REALITY_SNI" "$INBOUND_TAG" <<'PY'
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request

bot_env, public_ip, port, sni, tag = sys.argv[1:6]
port = int(port)

env = {}
for line in open(bot_env):
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("\"'")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(method, path, data=None, token=None):
    url = f"https://127.0.0.1:8000{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read())

form = urllib.parse.urlencode(
    {
        "username": env["MARZBAN_USERNAME"],
        "password": env["MARZBAN_PASSWORD"],
        "grant_type": "password",
    }
).encode()
req = urllib.request.Request(
    "https://127.0.0.1:8000/api/admin/token",
    data=form,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
    token = json.loads(resp.read())["access_token"]

hosts = api("GET", "/api/hosts", token=token)
for entries in hosts.values():
    for entry in entries:
        entry["address"] = public_ip
        entry["port"] = port
        entry["sni"] = sni
        entry["fingerprint"] = entry.get("fingerprint") or "chrome"
api("PUT", "/api/hosts", data=hosts, token=token)

users = api("GET", "/api/users?offset=0&limit=200", token=token).get("users", [])
for user in users:
    username = user.get("username", "")
    if not username.startswith("ct_"):
        continue
    proxies = user.get("proxies") or {}
    vless = dict(proxies.get("vless") or {})
    vless["flow"] = "xtls-rprx-vision"
    proxies["vless"] = vless
    api(
        "PUT",
        f"/api/user/{urllib.parse.quote(username)}",
        data={"proxies": proxies},
        token=token,
    )
    print("updated", username)
PY

if [[ -f "$BOT_ENV_FILE" ]]; then
  log "Setting MARZBAN_PROXIES flow for future orders"
  python3 - "$BOT_ENV_FILE" <<'PY'
import re
import sys

path = sys.argv[1]
line = "MARZBAN_PROXIES='{\"vless\":{\"flow\":\"xtls-rprx-vision\"}}'"
with open(path, encoding="utf-8") as handle:
    text = handle.read()
if re.search(r"^[ \t]*MARZBAN_PROXIES[ \t]*=", text, re.M):
    text = re.sub(r"^[ \t]*MARZBAN_PROXIES[ \t]*=.*$", line, text, flags=re.M)
else:
    text = text.rstrip() + "\n" + line + "\n"
with open(path, "w", encoding="utf-8") as handle:
    handle.write(text)
PY
  systemctl restart vpn-sales-bot >/dev/null 2>&1 || warn 'bot restart failed — run: systemctl restart vpn-sales-bot'
fi

log 'Done. Ask customers to re-import the subscription or use the new vless:// link.'
printf 'Reality now listens on %s:%s with SNI %s\n' "$PUBLIC_IP" "$REALITY_PORT" "$REALITY_SNI"
