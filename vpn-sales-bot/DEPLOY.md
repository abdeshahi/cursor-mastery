# Phase 1 VPS deployment

This does **not** deploy anything by itself. Follow the steps on the VPS when you are ready.

Do **not**:

- reinstall, replace, reconfigure, or containerize existing n8n
- publish PostgreSQL on `0.0.0.0`
- add Redis, Kubernetes, Grafana, Prometheus, or a Mini App

## What must run on the VPS

1. **Business PostgreSQL** (`vpn_sales`) — new Docker Compose project `vpn-sales`, container `vpn-sales-postgres`, bound to `127.0.0.1:5432`.
2. **Telegram bot** — Node.js 22 process, systemd unit `vpn-sales-bot`, production command `node dist/main.js`.
3. **Existing n8n 2.37.10** on port **5678** — leave it running. Add a Postgres credential in the n8n UI only.
4. **Existing Marzban** — no install; the bot calls its API.

The bot is **not** containerized. Only Postgres is.

n8n's own database (if it uses Docker Postgres internally) stays isolated. This stack uses a **different volume and database name**.

Suggested install path: `/opt/vpn-sales-bot`.

---

## Production checklist (before you start)

- [ ] n8n still answers `curl -fsS http://127.0.0.1:5678/healthz` (check only; do not restart n8n unless it is already down for unrelated reasons)
- [ ] Host port `5432` is free: `ss -lptn | grep 5432 || true` (n8n's internal Postgres is usually not published)
- [ ] Host port `3010` is free for the bot health endpoint
- [ ] Docker Engine is available (`docker compose version`)
- [ ] Node.js 22+ is available (`node -v`)
- [ ] `.env` is filled and **not** committed
- [ ] `POSTGRES_PASSWORD` is a long random value; `DATABASE_URL` uses the **same** password
- [ ] Telegram bot token is unique to this bot (not shared with another polling bot)
- [ ] `ADMIN_TELEGRAM_IDS` is your numeric Telegram user id
- [ ] Marzban URL is reachable from the VPS; `MARZBAN_PROXIES` / `MARZBAN_INBOUNDS` match the panel
- [ ] After start: `bash deploy/verify.sh` is all `OK`

---

## Environment

Copy `.env.example` to `.env` on the VPS. Required secrets:

| Variable | Used by |
|---|---|
| `POSTGRES_PASSWORD` | Compose + n8n credential |
| `DATABASE_URL` | Bot (must match user/password/db/port) |
| `BOT_TOKEN` | Bot + n8n Telegram node |
| `ADMIN_TELEGRAM_IDS` | Approve/Reject whitelist |
| `PAYMENT_CARD_NUMBER` / `PAYMENT_CARD_HOLDER` | Customer payment text |
| `MARZBAN_BASE_URL` / `MARZBAN_USERNAME` / `MARZBAN_PASSWORD` | Provisioning |

Optional: `TELEGRAM_PROXY`, `MARZBAN_SUBSCRIPTION_URL_PREFIX`, `MARZBAN_INBOUNDS`, `SUPPORT_USERNAME`, `DEFAULT_NODE`.

Generate a Postgres password on the VPS:

```bash
openssl rand -hex 24
```

Put it in **both** `POSTGRES_PASSWORD` and the password part of `DATABASE_URL`.

---

## n8n Postgres credential

See [deploy/n8n-postgres-credential.md](deploy/n8n-postgres-credential.md).

| Field | Value |
|---|---|
| Host | `vpn-sales-postgres` when using `docker-compose.n8n-access.yml`; else `127.0.0.1` |
| Port | `5432` |
| Database | `vpn_sales` |
| User | `vpn` |
| Password | `POSTGRES_PASSWORD` |
| SSL | disable |

Do not use n8n's own `n8n` database. Skip workflow 2 (payment notify); the bot already does it.

---

## Telegram and Marzban config check

Telegram: long polling. One process per bot token. `TELEGRAM_PROXY` only if `getMe` fails from the VPS.

Before the admin can receive receipts, each admin must press **Start** in the bot once. Telegram returns `chat not found` until then.

Marzban: `POST /api/admin/token` then `GET /api/system`. Create-user uses `MARZBAN_PROXIES` (default `{"vless":{}}`) and `MARZBAN_INBOUNDS` (`{}` = all inbounds for those protocols). If create-user returns 400 "Protocol vless is disabled", set proxies/inbounds to protocols your panel actually has.

### If Marzban is not installed yet

```bash
bash /opt/vpn-sales-bot/deploy/install-marzban.sh
# or, with a domain you own and DNS already pointing at the VPS:
MARZBAN_DOMAIN=panel.example.com bash /opt/vpn-sales-bot/deploy/install-marzban.sh
```

The script is safe to re-run and does not touch n8n or the vpn-sales stack. Two steps still need you:

```bash
marzban cli admin create --sudo     # pick username + password for the bot
```

Then open `http://<VPS_IP>:8000/dashboard` and create one VLESS inbound. Put the admin username/password into `MARZBAN_*` in `.env`.

Marzban listens on `8000` by default, so it does not clash with n8n on `5678`.

---

## Exact verification commands

Run as root on the VPS after deploy, or use `bash /opt/vpn-sales-bot/deploy/verify.sh`.

### PostgreSQL health

```bash
docker inspect --format='{{.State.Health.Status}}' vpn-sales-postgres
docker exec vpn-sales-postgres pg_isready -U vpn -d vpn_sales
docker exec vpn-sales-postgres psql -U vpn -d vpn_sales -c 'SELECT 1'
ss -lptn | grep 127.0.0.1:5432
```

### Application health

```bash
systemctl is-active vpn-sales-bot
curl -fsS http://127.0.0.1:3010/health
journalctl -u vpn-sales-bot -n 50 --no-pager
```

Expect `{"ok":true,"db":true,"service":"vpn-sales-bot"}`.

### Telegram bot

```bash
# loads BOT_TOKEN from .env; does not print the token
set -a && source /opt/vpn-sales-bot/.env && set +a
curl -fsS -m 15 ${TELEGRAM_PROXY:+-x "$TELEGRAM_PROXY"} \
  "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

Then send `/start` to the bot in Telegram.

### Marzban connectivity

```bash
set -a && source /opt/vpn-sales-bot/.env && set +a
curl -fsS -m 15 -X POST "${MARZBAN_BASE_URL%/}/api/admin/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=${MARZBAN_USERNAME}" \
  --data-urlencode "password=${MARZBAN_PASSWORD}" \
  --data-urlencode 'grant_type=password'
# then GET /api/system with the access_token (see deploy/verify.sh)
```

### n8n connectivity (read-only)

```bash
curl -fsS -m 10 http://127.0.0.1:5678/healthz
ss -lptn | grep 5678
```

Do not restart or recreate n8n as part of this deploy.

---

## Exact commands on the VPS

See the "EXACT DEPLOYMENT STEPS" in the agent summary, or run in order:

```bash
sudo mkdir -p /opt/vpn-sales-bot
sudo git clone <THIS_REPO_URL> /opt/vpn-sales-bot-src
sudo cp -a /opt/vpn-sales-bot-src/vpn-sales-bot/. /opt/vpn-sales-bot/
# or rsync the vpn-sales-bot folder
cd /opt/vpn-sales-bot
sudo cp .env.example .env
sudo nano .env
# install Node 22 if missing, then:
cd /opt/vpn-sales-bot
npm ci
npm run build
docker compose up -d
# optional, if docker network ls | grep n8n_default
# docker compose -f docker-compose.yml -f docker-compose.n8n-access.yml up -d
sudo cp deploy/vpn-sales-bot.service /etc/systemd/system/vpn-sales-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now vpn-sales-bot
bash deploy/verify.sh
```

Migrations run when the bot process starts (`runMigrations` in `src/main.ts`).
