#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  echo "Missing .env"
  exit 1
fi

# shellcheck disable=SC1091
source .env

PUBLIC_IP="$(curl -s ifconfig.me 2>/dev/null || echo 'UNKNOWN')"

cat > "${ROOT_DIR}/CREDENTIALS.md" <<EOF
# WordPress Stack — Credentials & Ports

> **توجه:** این فایل حاوی اطلاعات حساس است. در git commit نشود.

## Server

| Item | Value |
|------|-------|
| Public IP | ${PUBLIC_IP} |
| Timezone | ${TZ:-Asia/Tehran} |

## Ports

| Port | Protocol | Service | Exposure |
|------|----------|---------|----------|
| 22 | TCP | SSH | Host (firewall allowed) |
| 80 | TCP | Nginx HTTP | Host (firewall allowed) |
| 443 | TCP | Nginx HTTPS | Host (firewall allowed) |
| 3306 | TCP | MariaDB | localhost only (127.0.0.1) |
| 9000 | TCP | PHP-FPM | localhost only (127.0.0.1) |

## Database (MariaDB)

| Item | Value |
|------|-------|
| Host (from WordPress) | \`127.0.0.1:3306\` |
| Database | \`${MYSQL_DATABASE}\` |
| User | \`${MYSQL_USER}\` |
| Password | \`${MYSQL_PASSWORD}\` |
| Root Password | \`${MYSQL_ROOT_PASSWORD}\` |

## WordPress Admin

| Item | Value |
|------|-------|
| URL | \`http://${DOMAIN}/wp-admin\` |
| Username | \`${WORDPRESS_ADMIN_USER}\` |
| Password | \`${WORDPRESS_ADMIN_PASSWORD}\` |
| Email | \`${WORDPRESS_ADMIN_EMAIL}\` |

## SSL / Let's Encrypt

| Item | Value |
|------|-------|
| Domain | \`${DOMAIN}\` |
| Email | \`${LETSENCRYPT_EMAIL}\` |
| Cert path (on host) | \`certbot/conf/live/${DOMAIN}/\` |

## Backup

| Item | Value |
|------|-------|
| Schedule | Daily at 02:00 (cron) |
| Location | \`wordpress/backups/\` |
| Retention | ${BACKUP_RETENTION_DAYS:-7} days |

## Useful Commands

\`\`\`bash
cd wordpress
docker compose ps
docker compose logs -f nginx
./scripts/backup.sh
./scripts/init-ssl.sh
sudo ./scripts/setup-firewall.sh
\`\`\`
EOF

chmod 600 "${ROOT_DIR}/CREDENTIALS.md"
echo "Credentials written to ${ROOT_DIR}/CREDENTIALS.md"
