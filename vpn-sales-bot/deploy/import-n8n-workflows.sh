#!/usr/bin/env bash
# Import Phase 1 n8n credentials + workflows into the EXISTING n8n install.
# Does not reinstall n8n. Reads secrets from /opt/vpn-sales-bot/.env only.
#
# Usage (on VPS as root):
#   bash /opt/vpn-sales-bot/deploy/import-n8n-workflows.sh
set -euo pipefail
umask 077

N8N_APP=/opt/n8n-app
N8N_USER=n8n
BOT_ENV=/opt/vpn-sales-bot/.env
IMPORT_DIR=/tmp/vpn-sales-n8n-import
PROJECT_ID=7itV1t8r4OB29gvG
N8N=(sudo -u "$N8N_USER" bash -c "cd $N8N_APP && ./node_modules/.bin/n8n")

[[ -f "$BOT_ENV" ]] || { echo "ERROR: $BOT_ENV not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }

rm -rf "$IMPORT_DIR"
mkdir -m 700 -p "$IMPORT_DIR"
trap 'rm -rf "$IMPORT_DIR"' EXIT
python3 /opt/vpn-sales-bot/deploy/generate-n8n-import.py "$BOT_ENV" "$IMPORT_DIR"

echo "==> Stop n8n briefly (CLI needs port 5678 free)"
systemctl stop n8n.service
sleep 2
pkill -f "node ./node_modules/.bin/n8n" 2>/dev/null || true
sleep 1

CREDS_EXIST="$(python3 - <<'PY'
import sqlite3
c=sqlite3.connect("/opt/n8n-app/.n8n/.n8n/database.sqlite")
names={r[0] for r in c.execute("SELECT name FROM credentials_entity")}
print("yes" if {"VPN Sales Postgres", "VPN Sales Telegram"}.issubset(names) else "no")
PY
)"

echo "==> Import credentials"
if [[ "$CREDS_EXIST" == "yes" ]]; then
  echo "Already present — skipping"
else
  "${N8N[@]}" import:credentials --input="$IMPORT_DIR/credentials.json" --projectId="$PROJECT_ID"
fi

echo "==> Remove old VPN workflows"
python3 - <<'PY'
import sqlite3
c = sqlite3.connect("/opt/n8n-app/.n8n/.n8n/database.sqlite")
ids = [r[0] for r in c.execute("SELECT id FROM workflow_entity WHERE name LIKE 'VPN %'")]
for wf_id in ids:
    c.execute("DELETE FROM workflow_publish_history WHERE workflowId=?", (wf_id,))
    c.execute("DELETE FROM workflow_history WHERE workflowId=?", (wf_id,))
    c.execute("DELETE FROM shared_workflow WHERE workflowId=?", (wf_id,))
    c.execute("DELETE FROM workflow_entity WHERE id=?", (wf_id,))
c.commit()
print(f"removed {len(ids)} old workflow(s)")
PY

echo "==> Import workflows"
"${N8N[@]}" import:workflow --input="$IMPORT_DIR/workflows.json" --projectId="$PROJECT_ID"

echo "==> Publish workflows"
while IFS='|' read -r wf_id wf_name; do
  [[ -z "$wf_id" ]] && continue
  case "$wf_name" in
    VPN*) "${N8N[@]}" publish:workflow --id="$wf_id" ;;
  esac
done < <("${N8N[@]}" list:workflow)

echo "==> Start n8n again"
systemctl start n8n.service
sleep 8
curl -fsS -m 15 http://127.0.0.1:5678/healthz >/dev/null
echo "n8n healthz OK"

rm -rf "$IMPORT_DIR"
echo "==> Done. Four VPN workflows are active in n8n."
