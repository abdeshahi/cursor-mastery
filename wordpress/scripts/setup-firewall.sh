#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  SUDO="sudo"
else
  SUDO=""
fi

echo "Configuring firewall..."

if ${SUDO} ufw default deny incoming 2>/dev/null \
  && ${SUDO} ufw default allow outgoing 2>/dev/null \
  && ${SUDO} ufw allow 22/tcp comment 'SSH' 2>/dev/null \
  && ${SUDO} ufw allow 80/tcp comment 'HTTP' 2>/dev/null \
  && ${SUDO} ufw allow 443/tcp comment 'HTTPS' 2>/dev/null \
  && ${SUDO} ufw --force enable 2>/dev/null; then
  ${SUDO} ufw status verbose
  echo "UFW firewall configured: SSH (22), HTTP (80), HTTPS (443) allowed."
  exit 0
fi

echo "UFW unavailable in this environment — applying iptables rules instead..."

${SUDO} iptables -P INPUT DROP
${SUDO} iptables -P FORWARD DROP
${SUDO} iptables -P OUTPUT ACCEPT
${SUDO} iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
${SUDO} iptables -A INPUT -i lo -j ACCEPT
${SUDO} iptables -A INPUT -p tcp --dport 22 -j ACCEPT
${SUDO} iptables -A INPUT -p tcp --dport 80 -j ACCEPT
${SUDO} iptables -A INPUT -p tcp --dport 443 -j ACCEPT

${SUDO} iptables-save | ${SUDO} tee /etc/iptables.rules >/dev/null

echo "iptables rules applied: SSH (22), HTTP (80), HTTPS (443) allowed."
echo "To persist after reboot on Ubuntu: apt install iptables-persistent"
