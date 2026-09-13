#!/usr/bin/env bash
# Deploy from local machine to VPS via SSH (requires VPS_PASSWORD env var)
# Usage: VPS_PASSWORD='...' ./scripts/remote-deploy.sh root@1.2.3.4 [ssh_port]
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: VPS_PASSWORD='...' $0 user@host [port]"
  exit 1
fi

TARGET="$1"
PORT="${2:-22}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${VPS_PASSWORD:-}" ]]; then
  echo "Set VPS_PASSWORD environment variable."
  exit 1
fi

python3 << PY
import paramiko, sys, os
target = "${TARGET}"
port = int("${PORT}")
password = os.environ["VPS_PASSWORD"]
root = "${ROOT_DIR}"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(target.split("@")[1], port=port, username=target.split("@")[0], password=password, timeout=30, allow_agent=False, look_for_keys=False)

cmd = "curl -fsSL https://raw.githubusercontent.com/abdeshahi/cursor-mastery/cursor/wordpress-woocommerce-stack-72ff/wordpress/scripts/install-on-vps.sh | bash -s -- --domain cttel.ir --email admin@cttel.ir --title CTTEL"
stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
err = stderr.read().decode()
if err:
    print(err, file=sys.stderr)
code = stdout.channel.recv_exit_status()
client.close()
sys.exit(code)
PY
