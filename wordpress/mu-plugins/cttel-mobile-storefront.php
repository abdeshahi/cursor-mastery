<?php
/**
 * CTTEL mobile storefront — Hamrahtel-style UX (structure only, CTTEL branding).
 *
 * Replaces the legacy dedicated homepage mockup. Staging-safe; no production deploy hooks.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

if ( defined( 'CTTEL_MOBILE_STOREFRONT_BOOTSTRAPPED' ) ) {
	return;
}
define( 'CTTEL_MOBILE_STOREFRONT_BOOTSTRAPPED', true );
define( 'CTTEL_MOBILE_STOREFRONT_VERSION', '1.4.8-cart-qty-single' );

require_once __DIR__ . '/cttel-staging-wc-readiness.php';
require_once __DIR__ . '/cttel-mobile-storefront-assets.php';
require_once __DIR__ . '/cttel-mobile-storefront-shell.php';
require_once __DIR__ . '/cttel-mobile-storefront-home.php';
require_once __DIR__ . '/cttel-mobile-storefront-categories.php';
require_once __DIR__ . '/cttel-mobile-storefront-archive.php';
require_once __DIR__ . '/cttel-mobile-storefront-single.php';
require_once __DIR__ . '/cttel-mobile-storefront-cart-checkout.php';

/**
 * Whether the mobile shell (custom header + bottom nav) applies to this request.
 */
function cttel_mobile_storefront_uses_shell(): bool {
	if ( is_admin() || wp_doing_ajax() || wp_doing_cron() ) {
		return false;
	}
	if ( function_exists( 'is_cart' ) && ( is_cart() || is_checkout() ) ) {
		return false;
	}
	if ( is_front_page() ) {
		return true;
	}
	if ( cttel_mobile_storefront_is_categories_hub() ) {
		return true;
	}
	if ( function_exists( 'is_shop' ) && ( is_shop() || is_product_category() || is_product_tag() || is_product() ) ) {
		return true;
	}
	return false;
}
