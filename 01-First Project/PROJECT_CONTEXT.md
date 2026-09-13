# Project context

Goal: maximize internet speed on a home OpenWrt router using Mobinnet (Iran TD-LTE/LTE ISP) with V2Ray/Xray VPN.

## Hardware (from device Status → System)

- Model: Linksys EA8300 (Dallas)
- Target: `ipq40xx/generic` (Qualcomm IPQ4019)
- Firmware: OpenWrt 24.10.x
- Arch: ARMv7

## What we can automate from this repo

- Router-side OpenWrt optimizations via `openwrt/optimize-mobinnet-v2ray.sh`
  - flow offloading, packet steering, irqbalance, WAN MTU, BBR/sysctl

## What requires the user's router / credentials

- Applying the script (SSH to the LAN router)
- V2Ray/Xray server URI, UUID, Reality keys, and client package choice
