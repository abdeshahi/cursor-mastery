#!/bin/sh
# CTTEL homepage design: categories, menu, installment page, sample products.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

echo "==> Product categories..."
for cat in \
  "mobile:موبایل:0" \
  "headphones:هندزفری و AirPods:0" \
  "smartwatch:ساعت هوشمند:0" \
  "accessories:لوازم جانبی:0" \
  "gadgets:گجت:0"; do
  slug="${cat%%:*}"
  rest="${cat#*:}"
  name="${rest%%:*}"
  if ! WP term list product_cat --slug="${slug}" --field=term_id 2>/dev/null | grep -q '[0-9]'; then
    WP term create product_cat "${name}" --slug="${slug}" --description="دسته ${name} — تصویر را از محصولات → دسته‌ها اضافه کنید."
  fi
done

echo "==> Installment page..."
INST_ID="$(WP post list --post_type=page --name=installment --field=ID 2>/dev/null | head -1)"
INST_CONTENT='<!-- wp:group {"layout":{"type":"constrained","contentSize":"720px"},"style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem"}}}} -->
<div class="wp-block-group" style="padding-top:2rem;padding-bottom:2rem"><!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">خرید اقساطی CTTEL</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>موبایل، لوازم جانبی و گجت را با طرح‌های متنوع اقساطی تهیه کنید. این صفحه از <strong>برگه‌ها → خرید اقساطی</strong> قابل ویرایش است.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list"><li>مدارک ساده و فرآیند سریع</li><li>طرح‌های متنوع برای محصولات منتخب</li><li>پشتیبانی CTTEL در تمام مراحل</li></ul>
<!-- /wp:list -->

<!-- wp:buttons -->
<div class="wp-block-buttons"><!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="/shop/">مشاهده محصولات</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons --></div>
<!-- /wp:group -->'

if [ -z "${INST_ID}" ]; then
  INST_ID="$(WP post create --post_type=page --post_title='خرید اقساطی' --post_name=installment --post_status=publish --post_content="${INST_CONTENT}" --porcelain)"
else
  WP post update "${INST_ID}" --post_title='خرید اقساطی' --post_content="${INST_CONTENT}" --post_status=publish
fi

echo "==> Sample products (for homepage grids)..."
create_product() {
  title="$1"
  slug="$2"
  price="$3"
  cat_slug="$4"
  featured="$5"
  if WP post list --post_type=product --name="${slug}" --field=ID 2>/dev/null | grep -q '[0-9]'; then
    return 0
  fi
  pid="$(WP post create --post_type=product --post_title="${title}" --post_name="${slug}" --post_status=publish --porcelain)"
  WP post meta update "${pid}" _regular_price "${price}"
  WP post meta update "${pid}" _price "${price}"
  WP post meta update "${pid}" _stock_status instock
  WP post term set "${pid}" product_cat "${cat_slug}" 2>/dev/null || true
  if [ "${featured}" = "yes" ]; then
    WP post meta update "${pid}" _featured yes
    WP post meta update "${pid}" total_sales 25
  fi
}

create_product "آیفون 15" "iphone-15" "52000000" "mobile" "yes"
create_product "سامسونگ Galaxy S24" "galaxy-s24" "38000000" "mobile" "yes"
create_product "AirPods Pro" "airpods-pro" "12500000" "headphones" "yes"
create_product "ساعت Apple Watch" "apple-watch" "18000000" "smartwatch" "yes"
create_product "شارژر فندکی" "car-charger" "850000" "accessories" "no"
create_product "پاوربانک 20000" "powerbank-20k" "2200000" "gadgets" "no"
create_product "هدفون Bluetooth" "bt-headphone" "3500000" "headphones" "no"
create_product "گلس محافظ" "screen-guard" "450000" "accessories" "no"

echo "==> Main menu..."
MAIN_MENU="16"
WP menu item add-custom "${MAIN_MENU}" 'خرید اقساطی' 'https://cttel.ir/installment/' --position=2 2>/dev/null || true
WP menu item add-custom "${MAIN_MENU}" 'موبایل' 'https://cttel.ir/product-category/mobile/' --position=3 2>/dev/null || true
WP menu item add-custom "${MAIN_MENU}" 'لوازم جانبی' 'https://cttel.ir/product-category/accessories/' --position=4 2>/dev/null || true

echo "==> Footer widget..."
WP widget update text-1 --title='CTTEL' --text='<p><strong>فروشگاه CTTEL</strong></p><p>موبایل، گجت و لوازم جانبی — نقدی و اقساطی</p><p>تلفن: 021-00000000</p><p>آدرس: تهران — از ابزارک‌ها ویرایش کنید</p>' 2>/dev/null || true

echo "==> Homepage content..."
CONTENT="$(cat "${ROOT}/content/homepage-blocks.html")"
WP post update 24 --post_content="${CONTENT}" --post_status=publish

WP cache flush 2>/dev/null || true
echo "Homepage design deployed."
