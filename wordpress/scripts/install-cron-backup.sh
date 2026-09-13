#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_SCRIPT="${ROOT_DIR}/scripts/backup.sh"
CRON_LINE="0 2 * * * ${BACKUP_SCRIPT} >> /var/log/wp-backup.log 2>&1"
RENEW_LINE="0 3 * * * cd ${ROOT_DIR} && docker compose run --rm certbot renew --quiet && docker compose exec nginx nginx -s reload >> /var/log/wp-certbot-renew.log 2>&1"

TMP_CRON="$(mktemp)"
crontab -l 2>/dev/null > "${TMP_CRON}" || true

grep -Fq "${BACKUP_SCRIPT}" "${TMP_CRON}" || echo "${CRON_LINE}" >> "${TMP_CRON}"
grep -Fq "certbot renew" "${TMP_CRON}" || echo "${RENEW_LINE}" >> "${TMP_CRON}"

crontab "${TMP_CRON}"
rm -f "${TMP_CRON}"

echo "Cron jobs installed:"
crontab -l | grep -E 'backup|certbot' || true
