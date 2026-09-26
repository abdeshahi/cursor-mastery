#!/bin/sh
# Configure CTTEL storefront: Blocksy theme, menus, homepage blocks, WooCommerce pages.
# Run from repo root on VPS: ./scripts/setup-cttel-storefront.sh
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

echo "==> Installing Blocksy theme..."
WP theme install blocksy --activate 2>/dev/null || WP theme activate blocksy

echo "==> Installing Blocksy Companion (header/footer extensions)..."
if ! WP plugin is-installed blocksy-companion 2>/dev/null; then
  WP plugin install blocksy-companion --activate
else
  WP plugin activate blocksy-companion 2>/dev/null || true
fi

echo "==> Ensuring WooCommerce is active..."
WP plugin activate woocommerce 2>/dev/null || true

echo "==> Localizing WooCommerce page titles..."
for pair in "5:فروشگاه" "6:سبد خرید" "7:تسویه حساب" "8:حساب کاربری"; do
  id="${pair%%:*}"
  title="${pair##*:}"
  WP post update "${id}" --post_title="${title}" 2>/dev/null || true
done

echo "==> Store settings..."
WP option update woocommerce_currency 'IRR' 2>/dev/null || true
WP option update woocommerce_currency_pos 'right_space' 2>/dev/null || true
WP option update blogname 'فروشگاه CTTEL' 2>/dev/null || true
WP option update blogdescription 'تجهیزات و خدمات مخابراتی' 2>/dev/null || true

echo "==> Creating navigation menus..."
MAIN_MENU="$(WP menu list --format=csv 2>/dev/null | awk -F, '$2=="منوی اصلی"{print $1}' | head -1)"
if [ -z "${MAIN_MENU}" ]; then
  MAIN_MENU="$(WP menu create 'منوی اصلی' --porcelain)"
  WP menu item add-custom "${MAIN_MENU}" 'صفحه اصلی' 'https://cttel.ir/' --position=0
  WP menu item add-custom "${MAIN_MENU}" 'فروشگاه' 'https://cttel.ir/shop/' --position=1
  WP menu item add-custom "${MAIN_MENU}" 'سبد خرید' 'https://cttel.ir/cart/' --position=2
  WP menu item add-custom "${MAIN_MENU}" 'تسویه حساب' 'https://cttel.ir/checkout/' --position=3
  WP menu item add-custom "${MAIN_MENU}" 'حساب کاربری' 'https://cttel.ir/my-account/' --position=4
fi

FOOTER_MENU="$(WP menu list --format=csv 2>/dev/null | awk -F, '$2=="منوی فوتر"{print $1}' | head -1)"
if [ -z "${FOOTER_MENU}" ]; then
  FOOTER_MENU="$(WP menu create 'منوی فوتر' --porcelain)"
  WP menu item add-custom "${FOOTER_MENU}" 'فروشگاه' 'https://cttel.ir/shop/' --position=0
  WP menu item add-custom "${FOOTER_MENU}" 'سبد خرید' 'https://cttel.ir/cart/' --position=1
  WP menu item add-custom "${FOOTER_MENU}" 'حساب کاربری' 'https://cttel.ir/my-account/' --position=2
  WP menu item add-custom "${FOOTER_MENU}" 'حریم خصوصی' 'https://cttel.ir/privacy-policy/' --position=3
fi

WP menu location assign "${MAIN_MENU}" menu_1 2>/dev/null || \
  WP menu location assign "${MAIN_MENU}" primary 2>/dev/null || true
WP menu location assign "${FOOTER_MENU}" menu_2 2>/dev/null || \
  WP menu location assign "${FOOTER_MENU}" footer 2>/dev/null || true

echo "==> Creating homepage with Gutenberg blocks..."
HOMEPAGE_ID="$(WP post list --post_type=page --name=home --field=ID 2>/dev/null | head -1)"
CONTENT="$(cat "${ROOT}/content/homepage-blocks.html")"
if [ -z "${HOMEPAGE_ID}" ]; then
  HOMEPAGE_ID="$(WP post create \
    --post_type=page \
    --post_title='صفحه اصلی' \
    --post_name='home' \
    --post_status=publish \
    --post_content="${CONTENT}" \
    --porcelain)"
else
  WP post update "${HOMEPAGE_ID}" --post_title='صفحه اصلی' --post_content="${CONTENT}" --post_status=publish
fi

WP option update show_on_front 'page'
WP option update page_on_front "${HOMEPAGE_ID}"
WP option update page_for_posts '0'

echo "==> Blocksy design defaults (editable from Appearance → Customize)..."
WP theme mod set redirect_customizer 'blocksy' 2>/dev/null || true

echo "==> Flush rewrite rules and cache..."
WP rewrite structure '/%postname%/' 2>/dev/null || true
WP rewrite flush
WP cache flush 2>/dev/null || true

echo ""
echo "Done. Admin paths:"
echo "  Appearance → Customize  — colors, fonts, header, footer"
echo "  Pages → صفحه اصلی → Edit — homepage sections (blocks)"
echo "  Appearance → Menus      — header/footer menus"
echo "  Products                — WooCommerce catalog"
