# Rial Alert Bot

ربات تلگرام برای تحلیل اخبار فاندامنتال تأثیرگذار بر **ارزش ریال در بازار آزاد دلار/تومان** و ارسال هشدار جهت‌دار.

## هشدار مهم

- این ربات **پیش‌بینی قیمت قطعی** نمی‌دهد.
- سیگنال‌ها **قطعی و ۱۰۰٪ درست** نیستند.
- خروجی صرفاً برای آگاهی از فشار خبری است، نه توصیه سرمایه‌گذاری.

## جهت‌ها

| جهت | معنی |
|---|---|
| `rial_weaker` | فشار به سمت گران‌تر شدن دلار آزاد |
| `rial_stronger` | فشار به سمت ارزان‌تر شدن دلار آزاد |
| `neutral` | فقط خلاصه خبر |

## نصب

```bash
cd rial_alert_bot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## ساخت بات در BotFather

1. به [@BotFather](https://t.me/BotFather) بروید.
2. `/newbot` را بزنید و نام/یوزرنیم بدهید.
3. `BOT_TOKEN` را در `.env` قرار دهید.
4. (اختیاری) `TELEGRAM_ADMIN_IDS` را با آیدی عددی ادمین‌ها پر کنید.

## تنظیم LLM

API سازگار با OpenAI:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

می‌توانید OpenRouter / Groq / DeepSeek را با تغییر `LLM_BASE_URL` و `LLM_MODEL` استفاده کنید.

## اجرا

```bash
python -m app.main
```

## دستورات

| دستور | توضیح |
|---|---|
| `/start` | معرفی و ثبت کاربر |
| `/on` | روشن کردن هشدار |
| `/off` | خاموش کردن هشدار |
| `/status` | وضعیت سیستم |
| `/digest` | خلاصه فوری |
| `/sources` | لیست منابع |
| `/help` | راهنما |

### ادمین

- `/broadcast متن`
- `/pause_job`
- `/resume_job`

## منابع پیش‌فرض

- BBC فارسی business RSS (+ fallback HTML)
- تجارت‌نیوز
- دنیای اقتصاد
- اقتصاد آنلاین
- ایسنا اقتصاد

کلیدواژه‌ها و RSSها در `.env` قابل ویرایش هستند.

## تست

```bash
pytest -q
```

## Docker (اختیاری)

```bash
docker build -t rial-alert-bot .
docker run --env-file .env rial-alert-bot
```

## ساختار

```
rial_alert_bot/
  app/
    bot/          # handlers, formatters
    ingest/       # rss, html, telegram stub
    analysis/     # llm, scorer, aggregator
    storage/      # sqlite
    jobs/         # poll + digest
    services/     # rate provider, alert engine
```

## زمان‌بندی

- poll هر `POLL_SECONDS` (پیش‌فرض ۱۸۰ ثانیه)
- digest روزانه ۰۸:۳۰ و ۲۱:۰۰ به وقت `Asia/Tehran`
