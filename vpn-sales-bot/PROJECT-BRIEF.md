# VPN Sales MVP — Project Brief (Phase 1)

> Copy this entire file into another AI assistant for context continuity.

---

## 1. Project Summary

**Goal:** Telegram-based VPN sales MVP on a single VPS (Iran, Tehran).

**Stack:**
- Telegram bot (Node.js 22 + TypeScript + Telegraf) — sales, payments, provisioning
- PostgreSQL 16 (Docker) — business database `vpn_sales`
- Marzban + Xray — VPN panel, VLESS + Reality
- n8n 2.37.10 (existing, host install) — reminders, reports, health alerts
- nginx — HTTP subscription proxy on port 8090

**Repo:** `abdeshahi/cursor-mastery`  
**Branch:** `cursor/openwrt-mobinnet-optimize-1230`  
**PR:** https://github.com/abdeshahi/cursor-mastery/pull/1  
**App path on VPS:** `/opt/vpn-sales-bot`

---

## 2. VPS Environment

| Item | Value |
|------|-------|
| IP | `185.18.214.66` |
| Hostname | `server3.panel01.com` |
| Location | Tehran, Iran (AS48715 Sefroyek Pardaz) |
| OS | Ubuntu 24.04 |
| RAM | ~2 GB |
| Node.js | v24.19.0 (host, not Docker) |
| Docker | PostgreSQL + Marzban only |
| Bot Telegram | `@foxvpninbot` |

**Critical constraint:** Telegram API (`api.telegram.org`) is NOT reachable directly from VPS. Must use proxy:
```
TELEGRAM_PROXY=http://127.0.0.1:8118
```
(privoxy on host)

**Do NOT:** reinstall/modify n8n, containerize the bot, publish Postgres on 0.0.0.0.

---

## 3. Running Services & Ports

| Service | Port | Bind | Status |
|---------|------|------|--------|
| vpn-sales-bot (health) | 3010 | 127.0.0.1 | systemd `vpn-sales-bot.service` |
| PostgreSQL | 5432 | 127.0.0.1 | Docker `vpn-sales-postgres` |
| Marzban panel (HTTPS, self-signed) | 8000 | 0.0.0.0 | Docker `marzban-marzban-1` |
| Xray VLESS Reality | 443 | 0.0.0.0 | inside Marzban |
| nginx subscription proxy | 8090 | 0.0.0.0 | `/sub/*` → Marzban HTTPS |
| n8n | 5678 | existing | untouched |
| privoxy (Telegram proxy) | 8118 | 127.0.0.1 | existing |

**Marzban panel:** `https://185.18.214.66:8000/dashboard`  
**Marzban API admin:** user `vpnsalesbot` (sudo), credentials in `/root/marzban-api-admin.credentials` and `/opt/vpn-sales-bot/.env`

---

## 4. Purchase Flow (End-to-End)

```
Customer → Bot: Start / Buy VPN
Customer → Bot: Select plan
Bot → Customer: Card number + amount (card-to-card)
Customer → Bot: Photo/document receipt
Bot → Admin: Receipt + Approve/Reject inline buttons
Admin → Bot: Approve
Bot: order status paid → provisioning → completed
Bot → Marzban API: create user ct_{orderId}
Bot → Customer: vless:// link + setup instructions
```

**Order state machine:** `pending` → `waiting_payment` → `paid` → `provisioning` → `completed` | `failed` | `cancelled`

**Payment:** manual card-to-card only. No online gateway in Phase 1.

---

## 5. VPN Configuration (Current)

| Setting | Value |
|---------|-------|
| Protocol | VLESS + Reality (NOT vmess) |
| Port | 443 |
| SNI | `www.microsoft.com` |
| Flow | `xtls-rprx-vision` |
| Fingerprint | chrome |
| Server IP in config | `185.18.214.66` |
| Marzban username pattern | `ct_{orderId}` (e.g. `ct_1`) |

**Subscription URL format:** `http://185.18.214.66:8090/sub/{token}`  
**Subscription content:** base64-encoded single `vless://` line

**Important for clients:**
- v2rayNG (new versions) **blocks HTTP subscription URLs** → customers must use **Import config from clipboard** with `vless://` link, NOT subscription import
- NPV fails on HTTPS self-signed subscription → HTTP proxy on 8090 was added
- Marzban rotates `/sub/` tokens on restart → bot syncs URLs on startup (`syncSubscriptionUrls`)

---

## 6. Database Schema (PostgreSQL `vpn_sales`)

```
users           — telegram_id, username, status (active/blocked)
plans           — name, traffic_gb, duration_days, price (TOMAN)
orders          — user_id, plan_id, status, kind (new/renewal)
payments        — order_id, receipt_file_id, status (pending/approved/rejected)
subscriptions   — marzban_username, subscription_url, expire_at, status
reminder_logs   — for n8n renewal reminders (dedup)
alert_states    — for n8n Marzban health alerts (dedup)
schema_migrations
```

**Seeded plans:**
| Plan | Traffic | Duration | Price (TOMAN) |
|------|---------|----------|---------------|
| ۳۰ گیگ / ۳۰ روز | 30 GB | 30 days | 150,000 |
| ۵۰ گیگ / ۳۰ روز | 50 GB | 30 days | 200,000 |
| ۱۰۰ گیگ / ۳۰ روز | 100 GB | 30 days | 280,000 |
| ۱۰۰ گیگ / ۹۰ روز | 100 GB | 90 days | 750,000 |

Migrations: `migrations/001_init.sql`, `migrations/002_seed_plans.sql`  
Applied automatically on bot startup.

---

## 7. Codebase Structure

```
vpn-sales-bot/
├── src/
│   ├── main.ts                    — entry: migrate, sync subs, bot launch
│   ├── bot/
│   │   ├── create-bot.ts          — Telegraf handlers, menus, callbacks
│   │   ├── keyboards.ts           — inline keyboards
│   │   ├── messages.ts            — Persian UI strings
│   │   ├── health-server.ts       — GET /health on 3010
│   │   └── telegram-agent.ts      — HTTP proxy agent for Telegram
│   ├── services/
│   │   ├── sales-service.ts       — orders, payments, approve/reject, myServices
│   │   └── provisioning-service.ts — Marzban create user, delivery message, URL sync
│   ├── marzban/
│   │   └── client.ts              — API client, undici insecure TLS, fetchSubscriptionLinks
│   ├── database/
│   │   ├── repositories.ts        — all SQL queries
│   │   ├── migrate.ts             — migration runner
│   │   └── client.ts              — pg Pool
│   ├── config/
│   │   ├── env.ts                 — zod-validated env vars
│   │   └── logger.ts
│   └── utils/
│       ├── state-machine.ts       — order/payment state transitions
│       ├── provisioning.ts        — username, bytes, subscription URL resolve
│       ├── callback.ts            — encoded inline callback payloads
│       └── format.ts
├── migrations/
├── deploy/
│   ├── vpn-sales-bot.service      — systemd unit
│   ├── verify.sh                  — post-deploy health checks
│   ├── install-marzban.sh         — Marzban install + Reality inbound + bot .env
│   ├── install-subscription-proxy.sh — nginx :8090 for HTTP /sub/
│   ├── fix-reality-mobile-iran.sh — tune port/SNI/flow for Iranian mobile ISPs
│   ├── import-n8n-workflows.sh
│   └── generate-n8n-import.py
├── n8n/
│   ├── WORKFLOWS.md               — workflow specs + SQL queries
│   └── queries.sql
├── tests/                         — vitest, 18 tests
├── .env.example
├── DEPLOY.md
└── docker-compose.yml             — Postgres only
```

**Build:** `npm ci && npm run build` → `dist/`  
**Run:** `node dist/main.js` (via systemd)  
**Test:** `npm test`

---

## 8. Environment Variables (.env on VPS)

Required (secrets NOT listed here — in `/opt/vpn-sales-bot/.env` chmod 600):

```env
DATABASE_URL=postgres://vpn:***@127.0.0.1:5432/vpn_sales
BOT_TOKEN=***
ADMIN_TELEGRAM_IDS=162922662
PAYMENT_CARD_NUMBER=6104331171495311
PAYMENT_CARD_HOLDER=محمد فخراحمد
TELEGRAM_PROXY=http://127.0.0.1:8118

MARZBAN_BASE_URL=https://127.0.0.1:8000
MARZBAN_INSECURE_TLS=true
MARZBAN_USERNAME=vpnsalesbot
MARZBAN_PASSWORD=***
MARZBAN_PROXIES='{"vless":{"flow":"xtls-rprx-vision"}}'
MARZBAN_INBOUNDS='{}'
MARZBAN_SUBSCRIPTION_URL_PREFIX=http://185.18.214.66:8090
```

---

## 9. n8n Workflows (4 active, 1 skipped)

| # | Name | Schedule | Purpose |
|---|------|----------|---------|
| 1 | Renewal Reminder | daily 10:00 Tehran | 3-day and 1-day expiry reminders |
| 2 | Payment Notification | SKIP | bot handles this |
| 3 | Daily Sales Report | daily 21:00 | revenue/orders stats to admin |
| 4 | Marzban Health Alert | every 10 min | alert if Marzban API down |
| 5 | Lead Follow-up | daily 11:00 | follow up inactive users |

n8n Postgres credential: host `127.0.0.1`, db `vpn_sales`, user `vpn`.  
n8n Telegram nodes use HTTP Request + proxy `127.0.0.1:8118`.

Import: `bash /opt/vpn-sales-bot/deploy/import-n8n-workflows.sh`  
(requires brief `systemctl stop n8n` during CLI import)

---

## 10. Known Issues & Workarounds

| Issue | Cause | Current workaround |
|-------|-------|-------------------|
| Subscription import fails in v2rayNG | v2rayNG blocks HTTP sub URLs | Send `vless://` link; Import from clipboard |
| Subscription import fails in NPV (SSL error) | self-signed HTTPS on :8000 | HTTP proxy on :8090 (may still fail on some apps) |
| Ping -1ms on Hamrah-e Aval (MCI) mobile | ISP blocks datacenter IP or non-standard ports | Moved to port 443; may need Cloudflare Tunnel or IP change |
| Stale subscription URLs (404) | Marzban rotates tokens on restart | Bot syncs on startup + before delivery |
| `fetch failed` to Marzban | self-signed TLS | `MARZBAN_INSECURE_TLS=true` + undici in client.ts |
| Wrong IP in VLESS config | Marzban `{SERVER_IP}` used NAT outbound IP | Host Settings forced to `185.18.214.66` |
| Admin can't receive receipts | Admin never pressed Start in bot | Admin must /start the bot once |

---

## 11. Deploy / Ops Commands

```bash
# Full health check
bash /opt/vpn-sales-bot/deploy/verify.sh

# Rebuild & restart bot
cd /opt/vpn-sales-bot && npm ci && npm run build && systemctl restart vpn-sales-bot

# Marzban
marzban status
marzban restart
marzban logs

# Bot logs
journalctl -u vpn-sales-bot -f

# DB query
docker exec vpn-sales-postgres psql -U vpn -d vpn_sales -c "SELECT id, status FROM orders;"

# Tune Reality for Iranian mobile
bash /opt/vpn-sales-bot/deploy/fix-reality-mobile-iran.sh
# override: REALITY_PORT=443 REALITY_SNI=www.microsoft.com bash ...

# Install/repair HTTP subscription proxy
bash /opt/vpn-sales-bot/deploy/install-subscription-proxy.sh
```

---

## 12. Phase 1 Scope — IN vs OUT

**IN (done):**
- Telegram bot: buy, receipt, admin approve/reject, auto provisioning
- 4 VPN plans in DB
- Marzban VLESS Reality inbound
- PostgreSQL + migrations
- n8n automation (4 workflows)
- HTTP subscription proxy
- Health endpoint + verify script
- Unit tests (18 passing)

**OUT (not in scope):**
- Online payment gateway
- Telegram Mini App
- Web admin panel
- Domain + valid SSL cert
- Cloudflare Tunnel / CDN
- Redis, K8s, monitoring stack
- vmess / trojan / shadowsocks for customers (only VLESS Reality active)

---

## 13. Suggested Next Steps (Phase 2 candidates)

1. **Domain + Let's Encrypt** on nginx → fix subscription import in all clients
2. **Cloudflare Tunnel** → bypass MCI/datacenter IP blocking on mobile
3. **Rotate secrets** exposed in chat (bot token, VPS password, Marzban password)
4. **Online payment** (Zarinpal / IDPay) instead of manual card-to-card
5. **Admin web dashboard** for orders/subscriptions
6. **Multi-node** support (plan.node field exists but single node now)

---

## 14. Architecture Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Customer   │────▶│  Telegram Bot    │────▶│  PostgreSQL │
│  (Telegram) │◀────│  (Node.js :3010) │◀────│  (:5432)    │
└─────────────┘     └────────┬─────────┘     └──────┬──────┘
                             │                       │
┌─────────────┐              │                       │
│   Admin     │──────────────┘                       │
│  (Telegram) │                                      │
└─────────────┘              ┌─────────────┐          │
                             │   Marzban   │          │
                             │  API :8000  │          │
                             └──────┬──────┘          │
                                    │                 │
                             ┌──────▼──────┐          │
                             │    Xray     │          │
                             │ VLESS :443  │          │
                             └──────┬──────┘          │
                                    │                 │
┌─────────────┐     ┌───────────────▼──┐             │
│  v2rayNG /  │────▶│ Reality/TCP/443  │             │
│  NPV client │     └──────────────────┘             │
└─────────────┘                                      │
                                                     │
┌─────────────┐     ┌──────────────────┐             │
│    n8n      │────▶│   PostgreSQL     │◀────────────┘
│   :5678     │     └──────────────────┘
└─────────────┘

nginx :8090 ──proxy──▶ Marzban :8000/sub/*  (HTTP subscription for clients)
privoxy :8118 ──proxy──▶ api.telegram.org   (Telegram API for bot + n8n)
```

---

## 15. Key Files to Read First (for new AI)

1. `src/main.ts` — startup sequence
2. `src/services/sales-service.ts` — payment approve/reject
3. `src/services/provisioning-service.ts` — Marzban provisioning + delivery
4. `src/marzban/client.ts` — Marzban API + TLS + subscription fetch
5. `src/bot/create-bot.ts` — all Telegram UI flows
6. `deploy/verify.sh` — what "healthy" means
7. `migrations/001_init.sql` — full schema

---

*Last updated: 2026-09-11. VPS state reflects deployments through port 443 + subscription sync fixes.*
