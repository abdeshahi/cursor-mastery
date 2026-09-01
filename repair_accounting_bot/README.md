# ربات حسابداری تعمیرات (تلگرام)

ربات تلگرام برای **پذیرش تعمیرات** و **حسابداری مغازه موبایل** — فقط کاربرانی که شما مشخص می‌کنید دسترسی دارند.

## قابلیت‌ها

- **پذیرش جدید**: ثبت مشتری، دستگاه، ایراد، تعمیرکار، اجرت و قطعات
- **درصد تعمیرکار**: محاسبه خودکار سهم از اجرت
- **قطعات**: قیمت خرید از فروشنده + قیمت فروش به مشتری
- **بدهی مشتری**: جمع فاکتور منهای پرداخت‌های دریافتی
- **طلب قطعه‌فروش**: جمع خرید قطعات منهای پرداخت به فروشنده
- **گزارش**: جمع بدهی‌ها و لیست مشتریان بدهکار
- **دسترسی محدود**: فقط `ALLOWED_USER_IDS`

## فرمول حسابداری

| مورد | محاسبه |
|---|---|
| جمع مشتری | اجرت + فروش قطعات |
| بدهی مشتری | جمع مشتری − دریافت‌شده |
| طلب قطعه‌فروش | خرید قطعات − پرداخت به فروشنده |
| سهم تعمیرکار | اجرت × درصد |
| سود مغازه | جمع مشتری − خرید قطعات − سهم تعمیرکار |

## راه‌اندازی

```bash
cd repair_accounting_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# BOT_TOKEN و ALLOWED_USER_IDS را پر کنید
python -m app.main
```

### پیدا کردن Telegram User ID

به [@userinfobot](https://t.me/userinfobot) پیام `/start` بدهید و عدد `Id` را در `ALLOWED_USER_IDS` بگذارید.

### متغیرهای `.env`

| متغیر | توضیح |
|---|---|
| `BOT_TOKEN` | توکن بات از @BotFather |
| `ALLOWED_USER_IDS` | آیدی تلگرام کاربران مجاز (با کاما) |
| `ADMIN_USER_IDS` | ادمین برای `/addtech` و `/addsup` |
| `DATABASE_PATH` | مسیر فایل SQLite |

## دستورات

| دستور / دکمه | کار |
|---|---|
| 📝 پذیرش جدید | ثبت پرونده تعمیر |
| 📋 پرونده‌های باز | لیست تعمیرات جاری |
| 💰 گزارش بدهی‌ها | جمع بدهی مشتری و طلب قطعه‌فروش |
| 👥 بدهی مشتریان | لیست مشتریان بدهکار |
| `/repair 5` | جزئیات پرونده |
| `/addtech علی\|40` | افزودن تعمیرکار با درصد ۴۰ |
| `/addsup رضایی` | افزودن فروشنده قطعه |

## تست

```bash
pytest -q
```

## Deploy (systemd نمونه)

```ini
[Unit]
Description=Repair Accounting Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/repair_accounting_bot
EnvironmentFile=/opt/repair_accounting_bot/.env
ExecStart=/opt/repair_accounting_bot/.venv/bin/python -m app.main
Restart=always

[Install]
WantedBy=multi-user.target
```
