# راه‌اندازی وردپرس + ووکامرس با Docker

پشته سبک شامل **Nginx**، **MariaDB**، **WordPress فارسی**، **WooCommerce**، **SSL (Let's Encrypt)**، **فایروال** و **بکاپ روزانه**.

## پیش‌نیازها

- Ubuntu 22.04+ / Debian
- Docker Engine + Docker Compose plugin
- دامنه با رکورد A به IP سرور (برای SSL)

## نصب سریع

```bash
cd wordpress
chmod +x scripts/*.sh
./scripts/deploy.sh
```

## پورت‌ها

| پورت | سرویس | دسترسی |
|------|--------|--------|
| 22 | SSH | باز (فایروال) |
| 80 | HTTP / ACME | باز (فایروال) |
| 443 | HTTPS | باز (فایروال) |
| 3306 | MariaDB | فقط localhost (127.0.0.1) |
| 9000 | PHP-FPM | فقط localhost (127.0.0.1) |

## SSL (Let's Encrypt)

1. در `.env` مقدار `DOMAIN` و `LETSENCRYPT_EMAIL` را تنظیم کنید.
2. DNS دامنه را به IP سرور اشاره دهید.
3. اجرا:

```bash
./scripts/init-ssl.sh
```

## فایروال

```bash
sudo ./scripts/setup-firewall.sh
```

اول UFW را امتحان می‌کند؛ اگر در محیط شما UFW کار نکرد (مثلاً Cloud VM)، قوانین **iptables** جایگزین می‌شود.

## بکاپ روزانه

```bash
./scripts/install-cron-backup.sh   # نصب cron (ساعت 02:00)
./scripts/backup.sh                # بکاپ دستی
```

خروجی در `backups/YYYYmmdd_HHMMSS/`:
- `database.sql.gz`
- `wordpress-files.tar.gz`

## رمزها

پس از deploy، فایل `CREDENTIALS.md` (gitignore) با تمام رمزها ساخته می‌شود.

## ساختار

```
wordpress/
├── docker-compose.yml
├── .env                    # رمزها (تولید خودکار)
├── nginx/
├── certbot/
├── scripts/
├── backups/
└── docs/
```
