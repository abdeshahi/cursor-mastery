#!/bin/sh
# OpenWrt optimizer for Mobinnet (TD-LTE) + V2Ray/Xray on ipq40xx (e.g. Linksys EA8300)
# Run ON the router via SSH as root:
#   sh optimize-mobinnet-v2ray.sh
#
# Optional env vars:
#   WAN_MTU=1400          # try 1420 / 1400 / 1380 / 1360
#   WAN_IFACE=wan         # UCI logical interface name
#   INSTALL_IRQBALANCE=1  # 1=install irqbalance (default), 0=skip
#   APPLY_BBR=1           # 1=enable BBR if available (default)

set -eu

WAN_MTU="${WAN_MTU:-1400}"
WAN_IFACE="${WAN_IFACE:-wan}"
INSTALL_IRQBALANCE="${INSTALL_IRQBALANCE:-1}"
APPLY_BBR="${APPLY_BBR:-1}"
BACKUP_DIR="/root/openwrt-optimize-backup-$(date +%Y%m%d-%H%M%S)"

log() { printf '%s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

need_root() {
	[ "$(id -u)" -eq 0 ] || die "Run as root on the OpenWrt router (ssh root@192.168.1.1)."
}

need_openwrt() {
	[ -f /etc/openwrt_release ] || die "This does not look like OpenWrt."
	# shellcheck disable=SC1091
	. /etc/openwrt_release
	log "OpenWrt: ${DISTRIB_DESCRIPTION:-unknown} (${DISTRIB_TARGET:-unknown})"
}

backup_configs() {
	mkdir -p "$BACKUP_DIR"
	cp -a /etc/config/firewall /etc/config/network /etc/config/system "$BACKUP_DIR/" 2>/dev/null || true
	log "Backup saved to $BACKUP_DIR"
}

ensure_uci_option() {
	# ensure_uci_option <config> <type> <option> <value> [section_filter]
	# Finds first section of type, or creates anonymous section.
	_cfg="$1"
	_type="$2"
	_opt="$3"
	_val="$4"
	_sec="$(uci -q show "$_cfg" | sed -n "s/^\($_cfg\.@$_type\[[0-9]*\]\)=$_type$/\1/p" | head -n1)"
	if [ -z "$_sec" ]; then
		_sec="$(uci add "$_cfg" "$_type")"
		_sec="$_cfg.$_sec"
	fi
	uci set "${_sec}.${_opt}=${_val}"
}

enable_flow_offloading() {
	log "==> Enabling Software + Hardware flow offloading"
	# defaults section usually exists
	if ! uci -q get firewall.@defaults[0] >/dev/null; then
		uci add firewall defaults >/dev/null
	fi
	uci set firewall.@defaults[0].flow_offloading='1'
	uci set firewall.@defaults[0].flow_offloading_hw='1'
	# Keep MSS clamping helpful for LTE/TD-LTE tunnels
	uci set firewall.@defaults[0].mtu_fix='1'
}

enable_packet_steering() {
	log "==> Enabling Packet Steering on all CPUs"
	# OpenWrt 21+: globals section
	if ! uci -q get network.@globals[0] >/dev/null; then
		uci add network globals >/dev/null
	fi
	# '2' or '1' depending on version; '1' enables, newer builds accept packet_steering=2 for all CPUs
	# Prefer '1' for widest compatibility; try all-CPUs if option exists in docs as 2
	uci set network.@globals[0].packet_steering='1'
	# Some 24.10 builds use packet_steering=2 for "Enabled (all CPUs)"
	if grep -q "packet_steering" /rom/etc/config/network 2>/dev/null \
		|| uci -q get network.@globals[0].packet_steering >/dev/null; then
		uci set network.@globals[0].packet_steering='2' 2>/dev/null \
			|| uci set network.@globals[0].packet_steering='1'
	fi
}

set_wan_mtu() {
	log "==> Setting ${WAN_IFACE} MTU to ${WAN_MTU} (Mobinnet TD-LTE friendly)"
	if ! uci -q get "network.${WAN_IFACE}" >/dev/null; then
		log "WARN: network.${WAN_IFACE} not found. Skipping MTU. Set WAN_IFACE=... and re-run."
		uci show network | grep "=interface" || true
		return 0
	fi
	uci set "network.${WAN_IFACE}.mtu=${WAN_MTU}"
}

install_irqbalance() {
	[ "$INSTALL_IRQBALANCE" = "1" ] || { log "==> Skipping irqbalance"; return 0; }
	log "==> Installing/enabling irqbalance"
	if ! command -v irqbalance >/dev/null 2>&1; then
		opkg update
		opkg install irqbalance || log "WARN: irqbalance install failed (optional)."
	fi
	if [ -x /etc/init.d/irqbalance ]; then
		/etc/init.d/irqbalance enable
		/etc/init.d/irqbalance restart || /etc/init.d/irqbalance start || true
	fi
}

enable_bbr() {
	[ "$APPLY_BBR" = "1" ] || return 0
	log "==> Trying TCP BBR congestion control"
	if [ -d /sys/module/tcp_bbr ] || modprobe tcp_bbr 2>/dev/null; then
		sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null 2>&1 || true
		# Persist via sysctl.conf if present
		if [ -f /etc/sysctl.conf ]; then
			grep -q 'tcp_congestion_control' /etc/sysctl.conf \
				|| echo 'net.ipv4.tcp_congestion_control=bbr' >> /etc/sysctl.conf
		fi
		mkdir -p /etc/sysctl.d
		echo 'net.ipv4.tcp_congestion_control=bbr' > /etc/sysctl.d/99-bbr.conf
		log "BBR enabled (if kernel supports it)."
	else
		log "BBR module not available on this build; skipping."
	fi
}

tune_network_sysctl() {
	log "==> Applying light network sysctl tweaks"
	mkdir -p /etc/sysctl.d
	cat > /etc/sysctl.d/99-mobinnet-vpn.conf <<'EOF'
net.core.default_qdisc=fq
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_slow_start_after_idle=0
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
EOF
	sysctl -p /etc/sysctl.d/99-mobinnet-vpn.conf >/dev/null 2>&1 || true
}

commit_and_reload() {
	log "==> Committing UCI and reloading network/firewall"
	uci commit firewall
	uci commit network
	# Prefer service restarts over full reboot
	/etc/init.d/firewall restart || true
	# network restart briefly drops LAN; warn in summary
	/etc/init.d/network reload || /etc/init.d/network restart || true
}

print_status() {
	log ""
	log "======== RESULT ========"
	log "flow_offloading:    $(uci -q get firewall.@defaults[0].flow_offloading || echo n/a)"
	log "flow_offloading_hw: $(uci -q get firewall.@defaults[0].flow_offloading_hw || echo n/a)"
	log "mtu_fix:         $(uci -q get firewall.@defaults[0].mtu_fix || echo n/a)"
	log "packet_steering:    $(uci -q get network.@globals[0].packet_steering || echo n/a)"
	log "WAN MTU:            $(uci -q get network.${WAN_IFACE}.mtu || echo n/a)"
	log "irqbalance:         $(command -v irqbalance >/dev/null && echo installed || echo missing)"
	log "tcp_cc:             $(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo n/a)"
	log "backup:             $BACKUP_DIR"
	log ""
	log "Next steps:"
	log "  1) Speedtest WITHOUT VPN (LAN cable)."
	log "  2) Speedtest WITH VPN (LAN cable)."
	log "  3) If VPN is slow/unstable, re-run with lower MTU:"
	log "       WAN_MTU=1380 sh optimize-mobinnet-v2ray.sh"
	log "  4) Prefer Xray + VLESS + Reality over old VMESS/WS when possible."
	log "  5) Put heavy clients on 5GHz Wi-Fi or Ethernet."
	log ""
	log "Rollback example:"
	log "  cp -a $BACKUP_DIR/* /etc/config/ && /etc/init.d/network restart && /etc/init.d/firewall restart"
}

main() {
	need_root
	need_openwrt
	backup_configs
	enable_flow_offloading
	enable_packet_steering
	set_wan_mtu
	install_irqbalance
	enable_bbr
	tune_network_sysctl
	commit_and_reload
	print_status
	log "Done. LAN may blip for a few seconds during network reload."
}

main "$@"
