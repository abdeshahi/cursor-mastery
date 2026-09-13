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

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${ROOT_DIR}/backups/${TIMESTAMP}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

mkdir -p "${BACKUP_DIR}"

echo "[${TIMESTAMP}] Starting backup..."

docker compose exec -T db mysqldump \
  -u root \
  -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction \
  --routines \
  --triggers \
  "${MYSQL_DATABASE}" | gzip > "${BACKUP_DIR}/database.sql.gz"

docker compose exec -T wordpress tar czf - -C /var/www/html . > "${BACKUP_DIR}/wordpress-files.tar.gz"

echo "[${TIMESTAMP}] Backup saved to ${BACKUP_DIR}"

find "${ROOT_DIR}/backups" -mindepth 1 -maxdepth 1 -type d -mtime +"${RETENTION_DAYS}" -exec rm -rf {} +

echo "Old backups older than ${RETENTION_DAYS} days removed."
