#!/usr/bin/env bash
# نصب کامل WordPress + WooCommerce روی VPS اوبونتو/دبیان
# اجرا روی VPS (root یا sudo):
#   curl -fsSL https://raw.githubusercontent.com/abdeshahi/cursor-mastery/cursor/wordpress-woocommerce-stack-72ff/wordpress/scripts/install-on-vps.sh | sudo bash -s -- --domain cttel.ir --email admin@cttel.ir
set -euo pipefail

DOMAIN="cttel.ir"
EMAIL="admin@cttel.ir"
SITE_TITLE="CTTEL"
REPO="https://github.com/abdeshahi/cursor-mastery.git"
BRANCH="cursor/wordpress-woocommerce-stack-72ff"
INSTALL_DIR="/opt/cttel-wordpress"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain) DOMAIN="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    --title) SITE_TITLE="$2"; shift 2 ;;
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

log() { printf '\n==> %s\n' "$*"; }

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

log "System info"
uname -a
free -h
df -h /

log "Installing prerequisites"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git ufw iproute2 cron openssl

if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

systemctl enable docker 2>/dev/null || service docker start 2>/dev/null || true
sleep 2

log "Fetching WordPress stack"
rm -rf "${INSTALL_DIR}"
git clone --depth 1 --branch "${BRANCH}" "${REPO}" "${INSTALL_DIR}/repo"
cp -a "${INSTALL_DIR}/repo/wordpress" "${INSTALL_DIR}/app"
cd "${INSTALL_DIR}/app"
chmod +x scripts/*.sh

log "Generating environment"
./scripts/generate-env.sh
sed -i "s/^DOMAIN=.*/DOMAIN=${DOMAIN}/" .env
sed -i "s/^LETSENCRYPT_EMAIL=.*/LETSENCRYPT_EMAIL=${EMAIL}/" .env
sed -i "s|^WORDPRESS_SITE_TITLE=.*|WORDPRESS_SITE_TITLE=\"${SITE_TITLE}\"|" .env
sed -i "s/^WORDPRESS_ADMIN_EMAIL=.*/WORDPRESS_ADMIN_EMAIL=${EMAIL}/" .env

log "Deploying stack"
./scripts/deploy.sh

log "Configuring firewall"
./scripts/setup-firewall.sh

log "Installing backup cron"
# run as root — install for root crontab
./scripts/install-cron-backup.sh

PUBLIC_IP="$(curl -4 -fsS --max-time 5 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"

log "Done"
echo ""
echo "  Site:  http://${PUBLIC_IP}/"
echo "  Admin: http://${PUBLIC_IP}/wp-admin"
echo "  Credentials: ${INSTALL_DIR}/app/CREDENTIALS.md"
echo ""
echo "After DNS for ${DOMAIN} points to ${PUBLIC_IP}:"
echo "  cd ${INSTALL_DIR}/app && ./scripts/init-ssl.sh"
