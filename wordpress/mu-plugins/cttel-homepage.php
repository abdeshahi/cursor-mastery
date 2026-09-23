<?php
/**
 * CTTEL dedicated homepage — single presentation source (template layer).
 *
 * Replaces Gutenberg shortcode stack on the static front page.
 * Does not alter mobile off-canvas, cart, or WooCommerce logic.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

define( 'CTTEL_HOMEPAGE_VERSION', '2.0.1-final-mockup' );

require_once __DIR__ . '/cttel-homepage-render.php';

/** Whether the current request uses the dedicated homepage template. */
function cttel_is_dedicated_homepage(): bool {
	return is_front_page() && ! is_home();
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_is_dedicated_homepage() ) {
			$classes[] = 'cttel-dedicated-home';
		}
		return $classes;
	}
);

add_filter(
	'theme_page_templates',
	static function ( array $templates ): array {
		$templates['cttel-front-page.php'] = __( 'CTTEL Homepage (dedicated)', 'cttel-store' );
		return $templates;
	}
);

add_filter(
	'template_include',
	static function ( string $template ): string {
		if ( ! cttel_is_dedicated_homepage() ) {
			return $template;
		}
		$custom = __DIR__ . '/templates/cttel-front-page.php';
		return is_readable( $custom ) ? $custom : $template;
	},
	100
);

/** Prevent Blocksy page/article wrapper from injecting stored block content. */
add_filter(
	'the_content',
	static function ( string $content ): string {
		if ( cttel_is_dedicated_homepage() && in_the_loop() && is_main_query() ) {
			return '';
		}
		return $content;
	},
	1
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! cttel_is_dedicated_homepage() ) {
			return;
		}
		$css_path = __DIR__ . '/cttel-homepage.css';
		wp_register_style( 'cttel-homepage', false, array( 'cttel-design-system' ), CTTEL_HOMEPAGE_VERSION );
		wp_enqueue_style( 'cttel-homepage' );
		if ( is_readable( $css_path ) ) {
			wp_add_inline_style( 'cttel-homepage', (string) file_get_contents( $css_path ) );
		}
		$mockup_path = __DIR__ . '/cttel-home-mockup.css';
		if ( is_readable( $mockup_path ) ) {
			wp_add_inline_style( 'cttel-homepage', (string) file_get_contents( $mockup_path ) );
		}
	},
	30
);

/** Dedicated homepage: do not load legacy v2 section stylesheet. */
add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( cttel_is_dedicated_homepage() ) {
			wp_dequeue_style( 'cttel-home-v2' );
			wp_dequeue_style( 'cttel-storefront-polish' );
		}
	},
	100
);

add_filter(
	'bloginfo',
	static function ( $output, $show ) {
		if ( 'description' === $show && cttel_is_dedicated_homepage() ) {
			return 'انتخاب بهتر، دنیای هوشمندتر';
		}
		return $output;
	},
	10,
	2
);

add_filter(
	'woocommerce_product_add_to_cart_text',
	static function ( string $text ): string {
		if ( cttel_is_dedicated_homepage() ) {
			return __( 'افزودن به سبد', 'cttel-store' );
		}
		return $text;
	}
);
