# راهنمای مدیریت فروشگاه CTTEL از wp-admin

تمام تغییرات **روزمره ظاهر و محتوا** از پنل WordPress انجام می‌شود — بدون نیاز به Cursor یا ویرایش کد.

---

## فهرست سریع

| می‌خواهید… | مسیر دقیق wp-admin |
|------------|-------------------|
| لوگو | `ظاهر → سفارشی‌سازی → هویت سایت → Logo` |
| فونت متن/تیتر/دکمه | `ظاهر → سفارشی‌سازی → General → Typography` |
| فونت منو | `ظاهر → سفارشی‌سازی → Header → Menu → Font` |
| رنگ برند | `ظاهر → سفارشی‌سازی → General → Colors → Global Color Palette` |
| منو | `ظاهر → فهرست‌ها` |
| Header | `ظاهر → سفارشی‌سازی → Header Builder` |
| Footer | `ظاهر → سفارشی‌سازی → Footer Builder` |
| Hero / صفحه اصلی | `برگه‌ها → صفحه اصلی → ویرایش` |
| دسته‌بندی | `محصولات → دسته‌ها` |
| محصول / قیمت / موجودی | `محصولات → افزودن` یا ویرایش محصول |
| محصولات ویژه | ویرایش محصول → تیک «ویژه» |
| صفحه اقساط | `برگه‌ها → صفحه اصلی → ویرایش` → بخش «خرید اقساطی» |
| شبکه اجتماعی | `ظاهر → سفارشی‌سازی → General → Social Network Accounts` |
| اطلاعات تماس فوتر | `ظاهر → ابزارک‌ها → Footer Widget Area 1` |
| Copyright | `ظاهر → سفارشی‌سازی → Footer → Copyright` |

---

## 1. Typography (فونت)

**مسیر:** `ظاهر → سفارشی‌سازی → General → Typography`

| عنصر | تنظیم Customizer |
|------|----------------|
| متن عمومی | **Base Font** — فونت، اندازه، وزن |
| Headingها | **H1** تا **H6** — هر کدام جداگانه |
| دکمه‌ها | **Buttons** → Font / Size / Weight |
| منو | **Header Builder** → کلیک روی element **Menu** → Typography |

**پیش‌فرض فعلی:** Vazirmatn (قابل تغییر از پنل)

---

## 2. Colors (رنگ)

**مسیر:** `ظاهر → سفارشی‌سازی → General → Colors`

| رنگ | محل تنظیم |
|-----|-----------|
| Primary / Secondary / Accent | **Global Color Palette** — رنگ‌های ۱ تا ۳ |
| Background / Surface | پالت — رنگ‌های ۵ تا ۷ |
| Text اصلی | **Base Text** |
| Text ثانویه | **Muted Text** |
| Link | **Links** |
| Button | **Buttons** → Background / Text |
| Button hover | **Buttons** → Hover state |
| Header | **Header Builder** → row settings → Background |
| Footer | **Footer Builder** → row settings → Background |
| Product cards | **Customizer → WooCommerce → Product Archive** + **Single Product** |

---

## 3. Header

**مسیر:** `ظاهر → سفارشی‌سازی → Header Builder`

| عنصر | نحوه تغییر |
|------|-----------|
| Logo | `Site Identity → Logo` یا element **Logo** در Header Builder |
| Main menu | element **Menu** — منوی «منوی اصلی» |
| Search | element **Search** |
| Account | element **Account** |
| Cart | element **Cart** |
| Mobile menu | **Trigger** (آیکن hamburger) → offcanvas شامل **Mobile Menu** |
| Announcement bar | **Top Row** → افزودن element **Text** یا **HTML** |

---

## 4. Footer

**مسیر:** `ظاهر → سفارشی‌سازی → Footer Builder`

| عنصر | نحوه تغییر |
|------|-----------|
| ستون تماس | **Widget Area 1** ← محتوا در `ظاهر → ابزارک‌ها → Footer Widget Area 1` |
| منو | element **Menu** ← «منوی فوتر» |
| شبکه اجتماعی | element **Socials** + URLها در `General → Social Network Accounts` |
| Copyright | element **Copyright** |
| لوگو | افزودن **Widget** تصویر در Widget Area یا element Logo |

---

## 5. Homepage (صفحه اصلی)

**مسیر:** `برگه‌ها → صفحه اصلی → ویرایش`

| سکشن | بلوک Gutenberg | تغییر |
|------|----------------|-------|
| Hero | **Cover** | تصویر/رنگ پس‌زمینه، متن Heading، دکمه‌ها |
| Hero image | Cover → Background | آپلود از Media Library |
| Hero text | Heading + Paragraph | کلیک و تایپ |
| CTA buttons | Buttons | لینک و متن دکمه |
| Categories | **Product Categories** | تعداد ستون، نمایش/عدم نمایش |
| New products | **New Products** | تعداد محصول |
| Installment | **Columns** (بخش «خرید اقساطی») | متن هر ستون |
| Benefits | **Columns** (بخش «چرا CTTEL؟») | آیکن/متن کارت‌ها |
| Banner | **Cover** (بخش «پیشنهاد ویژه») | رنگ، متن، دکمه |

---

## 6. WooCommerce

| صفحه | URL | مدیریت |
|------|-----|--------|
| Shop | `/shop/` | `محصولات` + `دسته‌ها` |
| Product | `/product/...` | ویرایش هر محصول |
| Category | `/product-category/...` | `محصولات → دسته‌ها` |
| Cart | `/cart/` | خودکار — محتوا از سبد |
| Checkout | `/checkout/` | `WooCommerce → Settings → Checkout` |
| My Account | `/my-account/` | `WooCommerce → Settings → Accounts` |

**قیمت:** در تب **General** هر محصول — واحد **تومان**  
**موجودی:** تب **Inventory**  
**تخفیف:** تب **General → Sale price** یا **Marketing → Coupons**  
**ارسال:** `WooCommerce → Settings → Shipping`  
**پرداخت:** `WooCommerce → Settings → Payments`

---

## 7. واحد پول (تومان)

- **واحد نمایش:** تومان (`IRT`)
- **نحوه کار:** قیمت را به **تومان** وارد کنید (مثلاً `1500000`)
- **محاسبات WooCommerce** بدون تبدیل انجام می‌شود
- **درگاه پرداخت آینده:** معمولاً مبلغ × ۱۰ (ریال) در تنظیمات درگاه — بدون تغییر قیمت‌های فروشگاه

---

## 8. Mobile

- Header responsive: Header Builder → آیکن **موبایل/تبلت** برای preview
- منو موبایل: Trigger → Off-canvas Menu
- Product grid: `Customizer → WooCommerce → Product Archive → Columns` (responsive)

---

## 9. افزونه‌های فعال

| افزونه | وضعیت | ضرورت |
|--------|--------|--------|
| WooCommerce | فعال | **ضروری** |
| Blocksy Companion | فعال | **ضروری** (header/footer/account) |
| cttel-store (mu-plugin) | must-use | **ضروری** (نمایش تومان) |
| Akismet | غیرفعال | **قابل حذف** (اگر نظرات ندارید) |

---

## 10. Performance

- Elementor نصب **نیست**
- فقط JS/CSS مربوط به Blocksy + WooCommerce
- Lazy-load تصاویر: WordPress native (فعال)
- CSS سفارشی: خالی — همه از Customizer

---

## Design Tokens (Global)

| Token | مسیر Customizer |
|-------|----------------|
| `--theme-palette-color-*` | General → Colors → Palette |
| `--theme-font-*` | General → Typography |
| Container width | General → Layout → Maximum Site Width |
| Button radius | General → Buttons → Border Radius |
| Card radius | WooCommerce → Product Archive |

---

## اسکریپت‌های نگهداری (فقط سرور)

```bash
# راه‌اندازی اولیه فروشگاه
./scripts/setup-cttel-storefront.sh

# Audit و اصلاح header/footer/تومان
./scripts/audit-fix-storefront.sh
```

---

## چک‌لیست مالک فروشگاه (بدون کد)

- [ ] لوگو در Site Identity
- [ ] فونت Vazirmatn یا دلخواه در Typography
- [ ] رنگ برند در Color Palette
- [ ] لینک شبکه اجتماعی در Social Network Accounts
- [ ] تلفن/آدرس در Footer Widget Area 1
- [ ] تصویر Hero در صفحه اصلی
- [ ] حداقل یک دسته و محصول
