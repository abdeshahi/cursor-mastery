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
		if ( function_exists( 'cttel_is_dedicated_homepage' ) && cttel_is_dedicated_homepage() ) {
			return;
		}
		if ( ! is_front_page() ) {
			return;
		}
		$css = <<<'CSS'
body.cttel-v2-home article.page .entry-header,
body.cttel-v2-home .hero-section[data-type="type-2"] {
	display: none !important;
}

body.cttel-v2-home {
	--theme-content-vertical-spacing: 16px;
	background-color: var(--cttel-bg, #f5f7fb) !important;
}

/* Header — surface + typography (mobile trigger/cart order unchanged) */
#header.ct-header,
#header [data-row*="middle"] {
	background: var(--cttel-surface, #fff) !important;
	border-bottom: 1px solid var(--cttel-border, rgba(11, 31, 58, 0.08)) !important;
	box-shadow: 0 1px 0 rgba(11, 31, 58, 0.04);
}

#header [data-row*="middle"] {
	--height: 64px !important;
}

#header .site-title,
#header .site-title a {
	font-weight: 800;
	font-size: clamp(1.05rem, 4vw, 1.35rem) !important;
	color: var(--cttel-navy, #0b1f3a) !important;
	letter-spacing: -0.03em;
	text-transform: none !important;
}

#header [data-device="mobile"] [data-id="trigger"],
#header [data-device="mobile"] [data-id="search"],
#header [data-device="mobile"] [data-id="cart"] .ct-cart-item {
	min-width: 44px;
	min-height: 44px;
}

#header [data-device="mobile"] [data-id="cart"] .ct-label {
	font-size: 0.6875rem;
	font-weight: 700;
	text-transform: none;
	color: var(--cttel-navy);
}

#header [data-device="desktop"] [data-id="menu"] > ul {
	gap: 0.15rem 1.25rem;
}

#header [data-device="desktop"] [data-id="menu"] > ul > li > a {
	font-size: 0.8125rem !important;
	font-weight: 700 !important;
	text-transform: none !important;
	letter-spacing: 0;
	color: var(--cttel-text-secondary, #64748b) !important;
}

#header [data-device="desktop"] [data-id="menu"] > ul > li.current-menu-item > a,
#header [data-device="desktop"] [data-id="menu"] > ul > li.current_page_item > a {
	color: var(--cttel-brand-primary, #2563eb) !important;
}

#header [data-device="desktop"] [data-id="search"] {
	opacity: 0.85;
}

@media (min-width: 1000px) {
	#header [data-row*="middle"] {
		--height: 72px !important;
	}
}

body.cttel-v2-home #header .menu-item a[href*="/sample-page"],
body.cttel-v2-home #header .menu-item a[href*="/cart"],
body.cttel-v2-home #header .menu-item a[href*="/checkout"],
body.cttel-v2-home #header .menu-item a[href*="/my-account"],
body.cttel-v2-home #header .menu-item a[href="/shop/"],
body.cttel-v2-home #header .menu-item a[href$="/shop"] {
	display: none !important;
}

body.cttel-v2-home #header .menu-item:has(a[href*="/sample-page"]),
body.cttel-v2-home #header .menu-item:has(a[href*="/cart"]),
body.cttel-v2-home #header .menu-item:has(a[href*="/checkout"]),
body.cttel-v2-home #header .menu-item:has(a[href*="/my-account"]),
body.cttel-v2-home #header .menu-item:has(a[href$="/shop"]) {
	display: none !important;
}
CSS;
		wp_register_style( 'cttel-storefront-polish', false, array( 'cttel-design-system' ), '4.0.0' );
		wp_enqueue_style( 'cttel-storefront-polish' );
		wp_add_inline_style( 'cttel-storefront-polish', $css );
	},
	18
);
