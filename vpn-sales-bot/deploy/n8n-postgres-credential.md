# n8n Postgres credential for Phase 1 workflows

Use the **business** database `vpn_sales`. Do not point n8n workflows at n8n's own internal Postgres (`n8n` database).

Do not edit the existing n8n Docker Compose / systemd unit. Only add a credential inside the n8n UI.

## Values

Copy from `/opt/vpn-sales-bot/.env`:

| n8n credential field | Value |
|---|---|
| Host | `vpn-sales-postgres` if you started compose with `docker-compose.n8n-access.yml`; otherwise `127.0.0.1` if n8n runs on the host |
| Port | `5432` (or `POSTGRES_PORT` from `.env`) |
| Database | `vpn_sales` |
| User | `vpn` |
| Password | the `POSTGRES_PASSWORD` from `.env` |
| SSL | disable |
| SSH Tunnel | off |

If n8n is in Docker and `n8n_default` exists:

```bash
docker network ls | grep n8n
cd /opt/vpn-sales-bot
docker compose -f docker-compose.yml -f docker-compose.n8n-access.yml up -d
```

Then in n8n: Host = `vpn-sales-postgres`.

## Workflows

Follow `n8n/WORKFLOWS.md`. Skip payment notifications; the bot already sends those.
