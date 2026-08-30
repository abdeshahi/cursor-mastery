# CTTEL News Bot

بات خودکار برای دریافت آخرین اخبار از سایت‌های tech/mobile، ترجمه تخصصی به فارسی، و انتشار در کانال تلگرام.

## قابلیت‌ها

- دریافت خبر از RSS (پیش‌فرض: GSMArena, The Verge, TechCrunch, 9to5Google, Android Authority, Engadget)
- ترجمه تخصصی و روان با OpenAI-compatible API
- جلوگیری از ارسال تکراری (dedup)
- ارسال عکس شاخص در صورت وجود
- زمان‌بندی با cron
- health check روی پورت 3002

## راه‌اندازی

1. یک بات جدید از [@BotFather](https://t.me/BotFather) بسازید
2. بات را **Admin** کانال خود کنید (با دسترسی Post Messages)
3. فایل `.env` را از `.env.example` کپی کنید

```bash
cp .env.example .env
pnpm install
pnpm dev
```

### متغیرهای مهم

| متغیر | توضیح |
|---|---|
| `BOT_TOKEN` | توکن بات تلگرام |
| `CHANNEL_ID` | `@channel_username` یا `-100...` |
| `OPENAI_API_KEY` | کلید API برای ترجمه تخصصی |
| `FEED_URLS` | لیست RSS با کاما (اختیاری) |
| `POLL_CRON` | زمان‌بندی (پیش‌فرض: هر ۳۰ دقیقه) |
| `TELEGRAM_PROXY` | پروکسی برای VPS ایران (مثلاً `http://127.0.0.1:8118`) |

### افزودن سایت‌های دلخواه

در `.env`:

```env
FEED_URLS=https://example.com/rss,https://another.com/feed.xml
```

## Deploy روی VPS

```bash
VPS_PASSWORD=... python3 deploy/vps-deploy.py
```

سرویس systemd: `cttel-news-bot` روی پورت **3002**

## تست یک‌باره

```bash
pnpm poll-once
```

## نمونه خروجی کانال

```
📰 [عنوان فارسی]

[خلاصه ۲–۴ جمله‌ای روان]

📌 منبع: GSMArena
🗓 ۱۴۰۵/۰۶/۰۸، ۱۳:۳۰
🔗 مطالعه منبع
```

## نکات

- برای ترجمه تخصصی، `OPENAI_API_KEY` الزامی است
- اگر سایت RSS ندارد، آدرس feed XML آن را پیدا کنید یا به ما بگویید scraper اضافه کنیم
- برای جلوگیری از conflict با بات‌های دیگر، پورت 3002 و سرویس جداگانه استفاده شده
