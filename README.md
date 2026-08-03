# مدیریت فروشگاه سی‌تی‌تل

داشبورد فارسی و راست‌چین مدیریت فروشگاه موبایل؛ شامل فروش و فاکتورها، کالا و انبار، مشتریان، تعمیرات، گزارش‌ها و دسترسی نقش‌محور پرسنل.

## اجرای محلی

```bash
npm install
npm run dev
```

اگر متغیرهای Supabase تنظیم نشده باشند، برنامه در حالت نمایشی اجرا و اطلاعات داخل `localStorage` همان مرورگر ذخیره می‌شود.

## راه‌اندازی دیتابیس مرکزی

برای همگام‌شدن اطلاعات بین گوشی پرسنل:

1. در [Supabase](https://supabase.com) یک پروژه بسازید.
2. فایل `supabase/schema.sql` را در بخش **SQL Editor** اجرا کنید.
3. از مسیر **Authentication > Users** برای هر پرسنل یک حساب ایمیل و رمز عبور بسازید.
4. در صورت نیاز نقش کاربران را با یکی از مقادیر `admin`، `sales` یا `technician` تنظیم کنید:

```sql
update public.profiles
set role = 'admin'
where id = (select id from auth.users where email = 'manager@cttel.ir');
```

5. فایل `.env.example` را با نام `.env.local` کپی و آدرس پروژه و کلید عمومی Supabase را وارد کنید:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_KEY
```

کلید `service_role` را هرگز در این برنامه یا متغیرهای `VITE_` قرار ندهید.

## انتشار برای پرسنل

پروژه را در Vercel، Netlify یا Cloudflare Pages منتشر کنید و دو متغیر بالا را در تنظیمات سرویس میزبان وارد کنید. دستور ساخت `npm run build` و پوشه خروجی `dist` است. برنامه برای نصب PWA به HTTPS نیاز دارد که این سرویس‌ها به‌صورت خودکار فراهم می‌کنند.

پس از انتشار، پرسنل آدرس برنامه را روی گوشی باز می‌کنند:

- اندروید: منوی مرورگر ← **افزودن به صفحه اصلی / Install app**
- آیفون: دکمه **Share** در Safari ← **Add to Home Screen**

## سطح دسترسی

- `admin`: دسترسی کامل، گزارش‌ها و مدیریت دسترسی‌ها
- `sales`: فروش، مشتریان، مشاهده انبار و تعمیرات
- `technician`: مشتریان و مدیریت مراحل تعمیر
