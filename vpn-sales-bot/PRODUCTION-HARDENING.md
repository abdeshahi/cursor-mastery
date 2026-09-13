# Phase 1 production hardening

## Current network findings

- PostgreSQL is correctly published only as `127.0.0.1:5432`.
- Bot health is correctly bound to `127.0.0.1:3010`.
- Marzban uses host networking and `UVICORN_HOST="0.0.0.0"`, so its
  self-signed HTTPS panel/API on port 8000 is publicly reachable.
- Xray Reality must remain public on TCP 443.
- Trusted subscription HTTPS is public on port 8443 using a Let's Encrypt
  short-lived IP certificate.
- The transitional HTTP endpoint remains public on port 8090 for compatibility.

No production bind was changed automatically.

## Restrict Marzban safely

The bot and nginx both reach Marzban through `127.0.0.1:8000`, so binding
Uvicorn to localhost does not affect them or Xray's separate listener.
It does remove direct remote panel access.

Before changing it, verify SSH access and plan to use one of:

```bash
# Temporary panel access from an administrator workstation:
ssh -L 8000:127.0.0.1:8000 root@SERVER_IP
# Then open https://127.0.0.1:8000/dashboard and accept the private cert.
```

After confirming the tunnel, on the VPS:

```bash
cp -a /opt/marzban/.env /opt/marzban/.env.before-local-bind
sed -i 's/^UVICORN_HOST.*/UVICORN_HOST = "127.0.0.1"/' /opt/marzban/.env
marzban restart
ss -ltn | grep ':8000'
curl -fsSk https://127.0.0.1:8000/openapi.json >/dev/null
```

Expected bind: `127.0.0.1:8000`, not `0.0.0.0:8000`. Roll back with:

```bash
cp -a /opt/marzban/.env.before-local-bind /opt/marzban/.env
marzban restart
```

## PostgreSQL backups

Manual backup (defaults to seven retained files):

```bash
sudo /opt/vpn-sales-bot/deploy/backup-postgres.sh
```

Override retention or directory:

```bash
sudo RETENTION_COUNT=14 BACKUP_DIR=/var/backups/vpn-sales \
  /opt/vpn-sales-bot/deploy/backup-postgres.sh
```

Restore into a new, disposable database for testing. Never point this at the
live `vpn_sales` database:

```bash
BACKUP=/var/backups/vpn-sales/vpn_sales-YYYYMMDDTHHMMSSZ.dump
docker exec vpn-sales-postgres createdb -U vpn vpn_sales_restore_test
docker exec -i vpn-sales-postgres pg_restore \
  -U vpn -d vpn_sales_restore_test --no-owner --no-privileges < "$BACKUP"
docker exec vpn-sales-postgres psql -U vpn -d vpn_sales_restore_test \
  -c 'SELECT count(*) FROM orders;'
docker exec vpn-sales-postgres dropdb -U vpn vpn_sales_restore_test
```

Example daily systemd/cron scheduling is intentionally not installed
automatically. A root cron entry can run it once daily:

```cron
17 3 * * * /opt/vpn-sales-bot/deploy/backup-postgres.sh >>/var/log/vpn-sales-backup.log 2>&1
```

## Subscription transport

The bot sends `https://SERVER_IP:8443/sub/{token}`. The certificate is publicly
trusted and valid for the server IP, so modern v2rayNG/NPV clients do not need
cleartext HTTP or a private CA.

Let's Encrypt IP certificates are valid for 160 hours. Certbot's
`snap.certbot.renew.timer` must remain enabled, and
`/etc/letsencrypt/renewal-hooks/deploy/reload-vpn-sales-nginx` reloads nginx
after successful renewal. Verify with:

```bash
systemctl is-active snap.certbot.renew.timer
certbot renew --dry-run --cert-name vpn-sales-sub-ip --run-deploy-hooks
```

`http://SERVER_IP:8090/sub/{token}` remains transitional. Its bearer-like token
and configuration can be observed or modified on-path. Do not send this URL to
new customers, but do not remove it until old-client usage is checked.

For a future real domain:

1. Point a real DNS name to the VPS.
2. Obtain a Let's Encrypt certificate for that exact name.
3. Copy and edit `deploy/nginx-subscription-https.example.conf`.
4. Validate with `nginx -t`, then reload nginx.
5. Set `MARZBAN_SUBSCRIPTION_URL_PREFIX` to `https://<real-domain>`.
6. Restart the bot, verify client imports, then evaluate removal of port 8090.

Do not use a standard Cloudflare Tunnel as a transparent replacement for raw
VLESS Reality. It can front HTTP subscription traffic, but native Reality/TCP
requires an appropriate L4 design.

## Secrets checklist

Current checks:

- `.env` is gitignored.
- Production `.env` mode is `600` and owned by root.
- PostgreSQL is localhost-only.
- Current tracked files contain no detected Telegram bot token or VPS password.
- Scripts should log names/status only, never secret values.

If exposure is suspected, rotate manually in this order:

1. Telegram bot token (BotFather), then update bot/n8n credentials.
2. Marzban API admin password, then update bot `.env`.
3. PostgreSQL password, then update container, bot and n8n credential
   consistently during a maintenance window.
4. VPS/root password and all authorized SSH keys.
5. Any other API keys or proxy credentials.

Never paste rotated values into source control, command history, tickets, or
chat. Re-run `deploy/verify.sh` after each coordinated rotation.

## Supported Node.js

Node.js **24.x** is the supported runtime for development and production.
The VPS currently runs Node.js 24. Do not change production solely for this
hardening pass.
