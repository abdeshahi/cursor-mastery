<?php
/**
 * CTTEL front page bootstrap — legacy mockup DISABLED; mobile storefront owns the homepage.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

define( 'CTTEL_HOMEPAGE_VERSION', '3.0.0-mobile-storefront' );
define( 'CTTEL_LEGACY_HOMEPAGE_MOCKUP', false );

$cttel_staging_sync = __DIR__ . '/cttel-staging-home-sync.php';
if ( is_readable( $cttel_staging_sync ) ) {
	require_once $cttel_staging_sync;
}

$cttel_mobile_storefront = __DIR__ . '/cttel-mobile-storefront.php';
if ( is_readable( $cttel_mobile_storefront ) ) {
	require_once $cttel_mobile_storefront;
}

/** Whether the dedicated legacy mockup homepage is active (always false after v3). */
function cttel_is_dedicated_homepage(): bool {
	return false;
}

/** Mobile storefront is the active homepage presentation layer. */
function cttel_is_mobile_storefront_homepage(): bool {
	return is_front_page() && ! is_home();
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_is_mobile_storefront_homepage() ) {
			$classes[] = 'cttel-mobile-storefront-home';
		}
		return $classes;
	}
);

add_filter(
	'bloginfo',
	static function ( $output, $show ) {
		if ( 'description' === $show && cttel_is_mobile_storefront_homepage() ) {
			return 'فروشگاه آنلاین CTTEL';
		}
		return $output;
	},
	10,
	2
);
