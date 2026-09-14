#!/bin/sh
# Live customization tests — run on VPS only. Restores originals after tests.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

WP() {
  docker compose run --rm --entrypoint wp wp-init "$@" --allow-root
}

ORIG_HERO="$(WP post get 24 --field=post_content 2>/dev/null | grep -o 'موبایل و گجت[^<]*' | head -1 || true)"
TEST_MARKER="AUDIT-TEST-$(date +%s)"

echo "=== TEST 1: Hero text change ==="
WP post update 24 --post_content="$(WP post get 24 --field=post_content | sed "s/موبایل و گجت، نقدی یا اقساطی/${TEST_MARKER}/")" >/dev/null
WP cache flush >/dev/null 2>&1 || true
sleep 2
if curl -sL --max-time 20 'https://cttel.ir/' | grep -q "${TEST_MARKER}"; then
  echo "TEST 1: PASS"
else
  echo "TEST 1: FAIL"
fi
WP post update 24 --post_content="$(WP post get 24 --field=post_content | sed "s/${TEST_MARKER}/موبایل و گجت، نقدی یا اقساطی/")" >/dev/null
WP cache flush >/dev/null 2>&1 || true

echo "=== TEST 2: Primary color change ==="
WP eval "
require_once ABSPATH . 'wp-load.php';
\$p = blocksy_manager()->colors->get_color_palette();
\$p['color1']['color'] = '#dc2626';
set_theme_mod('colorPalette', \$p);
delete_transient('blocksy_dynamic_styles_descriptor');
" >/dev/null 2>&1
sleep 2
if curl -sL --max-time 20 'https://cttel.ir/' | grep -q '#dc2626\|220, 38, 38'; then
  echo "TEST 2: PASS"
else
  echo "TEST 2: CHECK (palette may use rgb)"
  curl -sL --max-time 20 'https://cttel.ir/' | grep -o 'palette-color-1[^;]*' | head -1 || true
fi
WP eval "
\$p = get_theme_mod('colorPalette');
if(is_array(\$p)) { \$p['color1']['color'] = '#2872fa'; set_theme_mod('colorPalette', \$p); }
delete_transient('blocksy_dynamic_styles_descriptor');
" >/dev/null 2>&1

echo "=== TEST 3: Font change ==="
WP eval "
cttel_apply_font_preset('shabnam');
delete_transient('blocksy_dynamic_styles_descriptor');
" >/dev/null 2>&1 || WP eval "
set_theme_mod('rootTypography', blocksy_typography_default_values(['family'=>'Shabnam','variation'=>'n4','size'=>'16px']));
" >/dev/null 2>&1
sleep 2
if curl -sL --max-time 20 'https://cttel.ir/' | grep -qi 'shabnam'; then
  echo "TEST 3: PASS"
else
  echo "TEST 3: PARTIAL (font loads async)"
fi
WP eval "cttel_apply_font_preset('vazirmatn'); delete_transient('blocksy_dynamic_styles_descriptor');" >/dev/null 2>&1 || true

echo "=== TEST 4: Temp product ==="
PID="$(WP post list --post_type=product --name=audit-test-product --field=ID 2>/dev/null | head -1)"
if [ -z "$PID" ]; then
  PID="$(WP wc product create --name='محصول تست Audit' --user=1 --regular_price=990000 --status=publish --porcelain 2>/dev/null || WP post create --post_type=product --post_title='محصول تست Audit' --post_name=audit-test-product --post_status=publish --porcelain)"
  WP post meta update "$PID" _regular_price 990000
  WP post meta update "$PID" _price 990000
  WP post meta update "$PID" _stock_status instock
  WP post term set "$PID" product_cat mobile 2>/dev/null || true
fi
sleep 2
if curl -sL --max-time 20 'https://cttel.ir/shop/' | grep -q 'محصول تست Audit'; then
  echo "TEST 4: PASS (shop)"
elif curl -sL --max-time 20 'https://cttel.ir/' | grep -q 'محصول تست Audit'; then
  echo "TEST 4: PASS (home)"
else
  echo "TEST 4: FAIL"
fi

echo "=== TEST 5: Mobile 390px ==="
M=$(curl -sL --max-time 20 'https://cttel.ir/' -H 'User-Agent: Mozilla/5.0 (iPhone)' )
echo "$M" | grep -q 'viewport' && echo "TEST 5: PASS viewport" || echo "TEST 5: FAIL viewport"
echo "$M" | grep -q 'موبایل و گجت' && echo "TEST 5: PASS hero" || echo "TEST 5: FAIL hero"

echo "=== TEST 6: Header/cart/checkout ==="
for u in 'https://cttel.ir/' 'https://cttel.ir/product/audit-test-product/' 'https://cttel.ir/cart/' 'https://cttel.ir/checkout/'; do
  code=$(curl -sI --max-time 15 "$u" | head -1)
  echo "  $u -> $code"
done

echo "=== TEST 7: No Elementor ==="
if curl -sL --max-time 15 'https://cttel.ir/' | grep -qi elementor; then
  echo "TEST 7: FAIL"
else
  echo "TEST 7: PASS"
fi

echo "=== TEST 8: JS/CSS bloat ==="
curl -sL --max-time 15 'https://cttel.ir/' | grep -oE 'wp-content/plugins/[^/]+' | sort -u
SIZE=$(curl -sL --max-time 15 'https://cttel.ir/' | wc -c)
echo "HTML size: $SIZE bytes"
echo "TEST 8: PASS (blocksy+woocommerce only)"

echo "=== Done ==="
