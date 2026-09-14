# راهنمای مدیریت ظاهر فروشگاه CTTEL

این فروشگاه طوری پیکربندی شده که **تمام تغییرات روزمره از پنل WordPress** انجام می‌شود — بدون نیاز به ویرایش کد.

---

## Proposed Theme

**نام:** Blocksy (رایگان)

**دلیل انتخاب:**
- سبک (~۳۰KB)، سازگار با WooCommerce و RTL فارسی
- **Header Builder** و **Footer Builder** داخل Customizer
- کنترل جداگانه فونت/رنگ برای body، headings، buttons، menu
- سبد خرید، حساب کاربری و جستجو در header به‌صورت پیش‌فرض
- بدون Elementor یا page builder سنگین

**قابلیت‌های پنل:**
| بخش | مسیر پنل |
|-----|----------|
| فونت و رنگ | `ظاهر → سفارشی‌سازی` |
| Header | `ظاهر → سفارشی‌سازی → Header` |
| Footer | `ظاهر → سفارشی‌سازی → Footer` |
| صفحه اصلی | `برگه‌ها → صفحه اصلی → ویرایش` |
| منو | `ظاهر → فهرست‌ها` |
| محصولات | `محصولات` |

---

## Required Plugins

| افزونه | کاربرد | ضروری؟ |
|--------|--------|--------|
| **WooCommerce** | فروشگاه، سبد، تسویه | بله (نصب شده) |
| **Blocksy Companion** | گسترش header/footer و بلوک‌های Blocksy | بله (رسمی و سبک) |

**نصب نشده (عمداً):** Elementor، WPBakery، Kirki جداگانه، افزونه‌های SEO/کش اضافی — تا سایت سبک بماند.

---

## Admin Editable Settings

### فونت
`ظاهر → سفارشی‌سازی → General → Typography`
- **Base Font** — متن عمومی (پیشنهاد: Vazirmatn)
- **Headings Font** — تیترها
- **Buttons Font** — دکمه‌ها
- **Menus Font** — منو
- وزن (Weight) و اندازه (Size) هر کدام جداگانه

### رنگ
`ظاهر → سفارشی‌سازی → General → Colors`
- Primary / Secondary / Accent
- Background / Surface (کارت‌ها)
- Text / Muted / Links
- Header / Footer / Button / Button Hover

### منو
`ظاهر → فهرست‌ها`
- **منوی اصلی** → موقعیت `Primary` (header)
- **منوی فوتر** → موقعیت `Secondary` (footer)
- افزودن/حذف/جابجایی آیتم، لینک سفارشی
- منوی موبایل همان منوی اصلی است (Responsive خودکار Blocksy)

### Header
`ظاهر → سفارشی‌سازی → Header Builder`
- لوگو: `Site Identity → Logo`
- منو، جستجو، سبد خرید، حساب کاربری — drag & drop
- نوار اطلاع‌رسانی (Top Bar): افزودن element متن/HTML

### Footer
`ظاهر → سفارشی‌سازی → Footer Builder`
- لوگو، منوی فوتر، widget area برای آدرس/تلفن
- Social Icons element
- Copyright text
- ستون‌ها با Footer Widget Areas

### Homepage
`برگه‌ها → صفحه اصلی → ویرایش با Block Editor`

سکشن‌های قابل ویرایش (بلوک Gutenberg):
| سکشن | نوع بلوک |
|------|----------|
| Hero | Cover + Heading + Buttons |
| دسته‌بندی | WooCommerce Product Categories |
| محصولات ویژه | WooCommerce New Products |
| اقساط | Columns (متن آزاد) |
| مزایا | Columns + Cards |
| بنر تبلیغاتی | Cover + Button |

### WooCommerce
| مورد | مسیر |
|------|------|
| دسته‌بندی | `محصولات → دسته‌ها` |
| محصول | `محصولات → افزودن` |
| تصویر/قیمت/موجودی | ویرایش هر محصول |
| ویژه / تخفیف | تب «Product data» |
| کوپن | `Marketing → Coupons` |
| ارسال | `WooCommerce → Settings → Shipping` |
| پرداخت | `WooCommerce → Settings → Payments` |

---

## Coding

### بدون کد (از پنل)
- فونت، رنگ، radius، container width، spacing
- لوگو، منو، header/footer
- تمام سکشن‌های صفحه اصلی
- محصولات، دسته‌ها، قیمت، کوپن
- CSS اضافی (در صورت نیاز): `ظاهر → سفارشی‌سازی → Additional CSS`

### نیازمند کد (فقط توسعه‌دهنده)
- تغییرات زیرساخت (Docker/Nginx/CDN)
- افزودن درگاه پرداخت سفارشی ایران
- قالب‌بندی پیچیده خارج از Blocksy/WooCommerce blocks

---

## Design Tokens (Global)

Blocksy مقادیر زیر را به **CSS Variables** تبدیل می‌کند — همه از Customizer:

```
--theme-palette-color-1 … primary
--theme-font-family … body
--theme-border-radius … buttons/cards
--theme-container-width … max width
```

---

## Mobile

تمام تنظیمات Customizer و Block Editor به‌صورت Responsive اعمال می‌شوند. Header Builder تنظیمات جداگانه Mobile/Tablet دارد.

---

## نصب مجدد / بازیابی

روی VPS:
```bash
cd /opt/cttel-wordpress/app
./scripts/setup-cttel-storefront.sh
```
