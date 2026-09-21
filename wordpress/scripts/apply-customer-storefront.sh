#!/bin/sh
# Apply CTTEL customer-ready storefront (homepage + Blocksy + menus + widgets).
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

echo "==> Blocksy theme (customer storefront)..."
WP theme activate blocksy 2>/dev/null || WP theme install blocksy --activate
WP plugin activate blocksy-companion 2>/dev/null || true

echo "==> WooCommerce shop live..."
WP option update woocommerce_coming_soon 'no' 2>/dev/null || true
WP option update woocommerce_store_pages_only 'no' 2>/dev/null || true
WP option update woocommerce_currency 'IRT' 2>/dev/null || true

echo "==> Remove demo Sample Page from nav..."
WP post update 2 --post_status=draft 2>/dev/null || true

echo "==> Deploy mu-plugins..."
docker exec wp_app mkdir -p /var/www/html/wp-content/mu-plugins
for f in cttel-store.php cttel-customizer.php cttel-quick-categories.php cttel-product-cards.php cttel-blocksy-mobile-offcanvas.php cttel-blocksy-mobile-header.php cttel-design-system.php cttel-homepage.php cttel-homepage-render.php cttel-home-sections.php cttel-home-products.php cttel-storefront-polish.php cttel-storefront-nav.php cttel-footer-branding.php; do
  [ -f "${ROOT}/mu-plugins/${f}" ] && \
    docker cp "${ROOT}/mu-plugins/${f}" "wp_app:/var/www/html/wp-content/mu-plugins/${f}"
done

echo "==> Site tagline..."
WP option update blogdescription 'موبایل و گجت — خرید نقدی و اقساطی' 2>/dev/null || true

echo "==> Main navigation (shop + categories + installment)..."
MAIN_MENU="$(WP menu list --format=csv 2>/dev/null | awk -F, '$2=="منوی اصلی"{print $1}' | head -1)"
if [ -n "${MAIN_MENU}" ]; then
  add_menu_item() {
    title="$1"
    url="$2"
    WP menu item list "${MAIN_MENU}" --format=csv 2>/dev/null | grep -q "${url}" && return 0
    WP menu item add-custom "${MAIN_MENU}" "${title}" "${url}" 2>/dev/null || true
  }
  add_menu_item 'فروشگاه' 'https://cttel.ir/shop/'
  add_menu_item 'موبایل' 'https://cttel.ir/product-category/mobile/'
  add_menu_item 'هندزفری' 'https://cttel.ir/product-category/headphones/'
  add_menu_item 'ساعت هوشمند' 'https://cttel.ir/product-category/smartwatch/'
  add_menu_item 'لوازم جانبی' 'https://cttel.ir/product-category/accessories/'
  add_menu_item 'گجت' 'https://cttel.ir/product-category/gadgets/'
  add_menu_item 'خرید اقساطی' 'https://cttel.ir/installment/'
fi

echo "==> Footer navigation..."
FOOTER_MENU="$(WP menu list --format=csv 2>/dev/null | awk -F, '$2=="منوی فوتر"{print $1}' | head -1)"
if [ -n "${FOOTER_MENU}" ]; then
  add_footer_item() {
    title="$1"
    url="$2"
    WP menu item list "${FOOTER_MENU}" --format=csv 2>/dev/null | grep -q "${url}" && return 0
    WP menu item add-custom "${FOOTER_MENU}" "${title}" "${url}" 2>/dev/null || true
  }
  add_footer_item 'فروشگاه' 'https://cttel.ir/shop/'
  add_footer_item 'حساب کاربری' 'https://cttel.ir/my-account/'
  add_footer_item 'خرید اقساطی' 'https://cttel.ir/installment/'
  add_footer_item 'حریم خصوصی' 'https://cttel.ir/privacy-policy/'
fi

echo "==> Footer widget (About + contact)..."
WP widget update block-1 --title='CTTEL' --content='<!-- wp:paragraph --><p><strong>فروشگاه CTTEL</strong></p><p>موبایل، گجت و لوازم جانبی — خرید نقدی و اقساطی با بیش از ۲۰ سال سابقه.</p><!-- /wp:paragraph --><!-- wp:paragraph --><p>تلفن: 021-00000000<br>آدرس: تهران — از ابزارک‌ها ویرایش کنید</p><!-- /wp:paragraph -->' 2>/dev/null || \
WP widget add block ct-footer-sidebar-1 1 --title='CTTEL' --content='<!-- wp:paragraph --><p><strong>فروشگاه CTTEL</strong></p><p>موبایل، گجت و لوازم جانبی — خرید نقدی و اقساطی.</p><!-- /wp:paragraph -->' 2>/dev/null || true

echo "==> Blocksy header/footer..."
docker cp "${ROOT}/scripts/blocksy-storefront-config.php" wp_app:/var/www/html/blocksy-storefront-config.php
docker compose run --rm --entrypoint wp wp-init eval-file /var/www/html/blocksy-storefront-config.php --allow-root
docker exec wp_app rm -f /var/www/html/blocksy-storefront-config.php

echo "==> Homepage content..."
CONTENT="$(cat "${ROOT}/content/homepage-blocks.html")"
WP post update 24 --post_content="${CONTENT}" --post_status=publish

echo "==> Brand placeholders (hero / categories / products)..."
if [ -x "${ROOT}/scripts/seed-brand-images.sh" ]; then
  "${ROOT}/scripts/seed-brand-images.sh"
fi

WP cache flush 2>/dev/null || true
echo "Customer storefront applied."
