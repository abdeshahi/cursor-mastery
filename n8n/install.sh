#!/usr/bin/env bash
# Install n8n on an Ubuntu/Debian VPS with Docker Compose + PostgreSQL.
# Usage (from this directory, as a user with sudo):
#   ./install.sh
# Optional:
#   N8N_HOST=n8n.example.com N8N_PROTOCOL=https WEBHOOK_URL=https://n8n.example.com/ ./install.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

docker_bin() {
  if docker info >/dev/null 2>&1; then
    docker "$@"
  elif command -v sudo >/dev/null 2>&1 && sudo -n docker info >/dev/null 2>&1; then
    sudo docker "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo docker "$@"
  else
    die "Docker is installed but this user cannot talk to the daemon. Add the user to the docker group and re-login."
  fi
}

compose() {
  docker_bin compose "$@"
}

detect_public_host() {
  local ip=""
  ip="$(curl -4 -fsS --max-time 5 https://ifconfig.me 2>/dev/null || true)"
  if [[ -z "$ip" ]]; then
    ip="$(curl -4 -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true)"
  fi
  if [[ -z "$ip" ]]; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi
  printf '%s' "${ip:-localhost}"
}

rand_secret() {
  openssl rand -hex 24
}

ensure_docker() {
  if docker info >/dev/null 2>&1 || { command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; }; then
    log "Docker is already running"
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    log "Starting Docker daemon"
    sudo systemctl enable --now docker
    return
  fi

  need_cmd curl
  command -v sudo >/dev/null 2>&1 || die "sudo is required to install Docker"
  log "Installing Docker Engine"
  curl -fsSL https://get.docker.com | sudo sh
  sudo systemctl enable --now docker
  if id -nG "$USER" | grep -qw docker; then
    :
  else
    sudo usermod -aG docker "$USER" || true
    log "Added $USER to the docker group. New shells will not need sudo."
  fi
}

ensure_env() {
  if [[ -f .env ]]; then
    log "Keeping existing n8n/.env (secrets are not overwritten)"
    return
  fi

  [[ -f .env.example ]] || die "n8n/.env.example is missing"
  need_cmd openssl
  cp .env.example .env

  local host protocol webhook
  host="${N8N_HOST:-$(detect_public_host)}"
  protocol="${N8N_PROTOCOL:-http}"
  if [[ -n "${WEBHOOK_URL:-}" ]]; then
    webhook="$WEBHOOK_URL"
  else
    webhook="${protocol}://${host}:${N8N_PORT:-5678}/"
  fi

  local enc pg_pass user_pass runner
  enc="$(openssl rand -hex 32)"
  pg_pass="$(rand_secret)"
  user_pass="$(rand_secret)"
  runner="$(rand_secret)"

  # Portable in-place edit without committing generated secrets to the example file.
  python3 - "$host" "$protocol" "$webhook" "$enc" "$pg_pass" "$user_pass" "$runner" <<'PY'
import pathlib, sys
host, protocol, webhook, enc, pg_pass, user_pass, runner = sys.argv[1:]
path = pathlib.Path(".env")
text = path.read_text()
replacements = {
    "N8N_HOST=": f"N8N_HOST={host}",
    "N8N_PROTOCOL=": f"N8N_PROTOCOL={protocol}",
    "WEBHOOK_URL=": f"WEBHOOK_URL={webhook}",
    "N8N_ENCRYPTION_KEY=": f"N8N_ENCRYPTION_KEY={enc}",
    "POSTGRES_USER=": "POSTGRES_USER=n8n",
    "POSTGRES_PASSWORD=": f"POSTGRES_PASSWORD={pg_pass}",
    "POSTGRES_NON_ROOT_USER=": "POSTGRES_NON_ROOT_USER=n8n_app",
    "POSTGRES_NON_ROOT_PASSWORD=": f"POSTGRES_NON_ROOT_PASSWORD={user_pass}",
    "RUNNERS_AUTH_TOKEN=": f"RUNNERS_AUTH_TOKEN={runner}",
}
lines = []
for line in text.splitlines():
    replaced = False
    for prefix, value in replacements.items():
        if line.startswith(prefix):
            lines.append(value)
            replaced = True
            break
    if not replaced:
        lines.append(line)
path.write_text("\n".join(lines) + "\n")
PY

  chmod 600 .env
  log "Wrote n8n/.env with generated secrets. Back this file up."
}

open_firewall() {
  if command -v ufw >/dev/null 2>&1 && sudo ufw status 2>/dev/null | grep -qi "Status: active"; then
    local port
    port="$(grep -E '^N8N_PORT=' .env | cut -d= -f2-)"
    port="${port:-5678}"
    log "Allowing TCP $port through ufw"
    sudo ufw allow "${port}/tcp" || true
  fi
}

wait_healthy() {
  local port
  port="$(grep -E '^N8N_PORT=' .env | cut -d= -f2-)"
  port="${port:-5678}"
  log "Waiting for n8n on port $port"
  local i
  for i in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:${port}/healthz" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  compose logs --tail=80 n8n postgres || true
  die "n8n did not become healthy in time"
}

main() {
  need_cmd curl
  chmod +x "$ROOT/init-data.sh"
  ensure_docker
  ensure_env
  open_firewall

  log "Pulling images and starting n8n"
  compose up -d

  wait_healthy

  local host protocol port webhook
  host="$(grep -E '^N8N_HOST=' .env | cut -d= -f2-)"
  protocol="$(grep -E '^N8N_PROTOCOL=' .env | cut -d= -f2-)"
  port="$(grep -E '^N8N_PORT=' .env | cut -d= -f2-)"
  webhook="$(grep -E '^WEBHOOK_URL=' .env | cut -d= -f2-)"

  cat <<EOF

n8n is running.

  Editor:  ${protocol}://${host}:${port}
  Health:  http://127.0.0.1:${port}/healthz
  Webhook: ${webhook}

Open the editor and create the first owner account.
Open TCP ${port} on the VPS firewall / security group if it is still blocked.

Useful commands (from ${ROOT}):
  docker compose ps
  docker compose logs -f n8n
  docker compose pull && docker compose up -d
  docker compose down          # keeps data volumes
EOF
}

main "$@"
