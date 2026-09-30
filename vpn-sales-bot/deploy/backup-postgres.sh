#!/usr/bin/env bash
# Create a compressed, timestamped backup of the business PostgreSQL database.
set -euo pipefail
umask 077

BACKUP_DIR="${BACKUP_DIR:-/var/backups/vpn-sales}"
RETENTION_COUNT="${RETENTION_COUNT:-7}"
CONTAINER="${POSTGRES_CONTAINER:-vpn-sales-postgres}"
POSTGRES_USER="${POSTGRES_USER:-vpn}"
POSTGRES_DB="${POSTGRES_DB:-vpn_sales}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FINAL="${BACKUP_DIR}/${POSTGRES_DB}-${STAMP}.dump"
TEMP="${FINAL}.tmp"

log() { printf '[vpn-sales-backup] %s\n' "$*"; }
fail() { printf '[vpn-sales-backup] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$RETENTION_COUNT" =~ ^[1-9][0-9]*$ ]] || fail 'RETENTION_COUNT must be a positive integer'
command -v docker >/dev/null 2>&1 || fail 'docker is required'
docker inspect "$CONTAINER" >/dev/null 2>&1 || fail "container ${CONTAINER} not found"

install -d -m 700 "$BACKUP_DIR"
trap 'rm -f "$TEMP"' EXIT

log "creating ${FINAL}"
if ! docker exec "$CONTAINER" pg_dump \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges >"$TEMP"; then
  fail 'pg_dump failed'
fi

[[ -s "$TEMP" ]] || fail 'pg_dump produced an empty file'
chmod 600 "$TEMP"
mv "$TEMP" "$FINAL"

mapfile -t BACKUPS < <(
  printf '%s\n' "$BACKUP_DIR"/"$POSTGRES_DB"-*.dump |
    while IFS= read -r file; do [[ -f "$file" ]] && printf '%s\n' "$file"; done |
    sort -r
)
if ((${#BACKUPS[@]} > RETENTION_COUNT)); then
  for old in "${BACKUPS[@]:RETENTION_COUNT}"; do
    rm -f -- "$old"
    log "removed expired backup ${old}"
  done
fi

log "backup complete: ${FINAL} ($(du -h "$FINAL" | cut -f1))"
