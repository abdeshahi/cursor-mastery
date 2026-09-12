# بهینه‌سازی OpenWrt برای مبین‌نت + V2Ray/Xray

برای روترهایی مثل **Linksys EA8300** با OpenWrt (`ipq40xx`) و اینترنت **مبین‌نت**.

> این محیط ابری به روتر منزل شما دسترسی SSH ندارد.  
> اسکریپت را **روی خود روتر** (SSH به‌عنوان `root`) اجرا کنید.

## یک‌دستوره (از لپ‌تاپ/PC)

اگر روتر در شبکه محلی‌تان است (`192.168.1.1`):

```bash
scp "01-First Project/openwrt/optimize-mobinnet-v2ray.sh" root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "sh /tmp/optimize-mobinnet-v2ray.sh"
```

یا مستقیم با کپی محتوا داخل SSH روتر:

```bash
ssh root@192.168.1.1
# سپس فایل را بسازید و اجرا کنید:
sh /tmp/optimize-mobinnet-v2ray.sh
```

## اسکریپت چه کار می‌کند؟

1. بکاپ از `/etc/config/{firewall,network,system}`
2. روشن کردن **Software + Hardware Flow Offloading**
3. روشن کردن **Packet Steering**
4. تنظیم **MTU=1400** روی اینترفیس `wan` (مناسب مبین‌نت/TD-LTE)
5. فعال بودن **MSS clamping** (`mtu_fix`)
6. نصب/فعال‌سازی **irqbalance**
7. فعال‌سازی **BBR** (اگر کرنل پشتیبانی کند)
8. چند تنظیم سبک `sysctl` برای TCP

## اگر هنوز کند بود

MTU را پایین‌تر امتحان کنید:

```bash
WAN_MTU=1380 sh /tmp/optimize-mobinnet-v2ray.sh
# یا
WAN_MTU=1360 sh /tmp/optimize-mobinnet-v2ray.sh
```

اگر نام اینترفیس WAN شما `wan` نیست:

```bash
WAN_IFACE=wwan WAN_MTU=1400 sh /tmp/optimize-mobinnet-v2ray.sh
```

## V2Ray / Xray (سرعت واقعی VPN)

اسکریپت کانفیگ سرور VPN شما را تغییر نمی‌دهد (چون آدرس/UUID سرور لازم است).  
برای حداکثر سرعت روی این سخت‌افزار:

| اولویت | پیشنهاد |
|--------|---------|
| بهترین | **Xray + VLESS + Reality + Vision** |
| خوب | Trojan / VLESS + TLS |
| معمولاً کندتر | VMESS + WebSocket + CDN سنگین |

- به‌جای V2Ray قدیمی، **Xray-core** (`armv7`) استفاده کنید.
- Multiplex را مگر ضرورت خاموش نگه دارید.
- اول با **کابل LAN** تست کنید؛ بعد Wi‑Fi 5GHz.

## تست تشخیص گلوگاه

1. بدون VPN + کابل → سقف مبین‌نت  
2. با VPN + کابل → اگر کم شد: پروتکل/سرور/MTU  
3. با VPN + Wi‑Fi → اگر فقط اینجا کم شد: وایرلس

## Rollback

مسیر بکاپ در خروجی اسکریپت چاپ می‌شود، مثلاً:

```bash
cp -a /root/openwrt-optimize-backup-YYYYMMDD-HHMMSS/* /etc/config/
/etc/init.d/network restart
/etc/init.d/firewall restart
```
