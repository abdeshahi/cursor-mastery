<?php
/**
 * CTTEL storefront visual polish — scoped CSS only (no header builder changes).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! is_front_page() ) {
			return;
		}
		$css = <<<'CSS'
/* Header surface only — mobile menu behavior unchanged */
#header.ct-header,
#header [data-row*="middle"] {
	background: var(--cttel-surface, #fff) !important;
	border-bottom: 1px solid var(--cttel-border, rgba(15, 23, 42, 0.08));
	box-shadow: none;
}
#header [data-device="mobile"] [data-id="trigger"],
#header [data-device="mobile"] [data-id="search"],
#header [data-device="mobile"] [data-id="cart"] .ct-cart-item {
	min-width: 44px;
	min-height: 44px;
}
#header .site-title,
#header .site-title a {
	font-weight: 800;
	color: var(--cttel-navy, #0b1f3a);
	letter-spacing: -0.02em;
}
CSS;
		wp_register_style( 'cttel-storefront-polish', false, array( 'cttel-design-system' ), '3.0.0' );
		wp_enqueue_style( 'cttel-storefront-polish' );
		wp_add_inline_style( 'cttel-storefront-polish', $css );
	},
	18
);
