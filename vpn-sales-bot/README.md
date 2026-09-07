# VPN Sales Bot — Phase 1

Telegram bot that sells VPN subscriptions. PostgreSQL is the business source of truth. Marzban only provisions accounts. Existing n8n on the VPS (port 5678) only sends reminders and reports.

**Deploy:** see [DEPLOY.md](DEPLOY.md). Do not reinstall n8n.

## What runs on the VPS

| Component | How |
|---|---|
| Business PostgreSQL `vpn_sales` | Docker Compose in this folder (Postgres **only**) |
| Telegram bot | Node.js + systemd `vpn-sales-bot` |
| n8n 2.37.10 | Already running — do not touch the service |
| Marzban | Existing panel — API only |

## Production start

```bash
npm ci
npm run build
npm start
# systemd: node /opt/vpn-sales-bot/dist/main.js
```

Migrations run automatically on bot start.

Plan prices live in PostgreSQL:

```sql
UPDATE plans SET price = 180000 WHERE id = 1;
```
