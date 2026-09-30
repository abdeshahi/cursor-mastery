<?php
/**
 * Blocksy mobile header — RTL hamburger on the right (Header Builder order).
 *
 * Mobile middle row (RTL, right → left):
 * [ Hamburger ] [ Logo ] [ Search ] [ Cart ]
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * @param array<string, mixed>|mixed $header Blocksy header_placements theme mod.
 * @return array<string, mixed>|mixed
 */
function cttel_blocksy_mobile_header_placements( $header ) {
	if ( ! is_array( $header ) || empty( $header['sections'] ) ) {
		return $header;
	}

	foreach ( $header['sections'] as &$section ) {
		if ( 'type-1' !== ( $section['id'] ?? '' ) ) {
			continue;
		}
		if ( empty( $section['mobile'] ) || ! is_array( $section['mobile'] ) ) {
			continue;
		}

		foreach ( $section['mobile'] as &$row ) {
			if ( 'middle-row' !== ( $row['id'] ?? '' ) ) {
				continue;
			}
			if ( empty( $row['placements'] ) || ! is_array( $row['placements'] ) ) {
				continue;
			}

			foreach ( $row['placements'] as &$placement ) {
				if ( 'start' === ( $placement['id'] ?? '' ) ) {
					$placement['items'] = array( 'trigger', 'logo' );
				}
				if ( 'end' === ( $placement['id'] ?? '' ) ) {
					$placement['items'] = array( 'search', 'cart' );
				}
			}
			unset( $placement );
		}
		unset( $row );
	}
	unset( $section );

	return $header;
}

add_filter( 'theme_mod_header_placements', 'cttel_blocksy_mobile_header_placements', 20 );

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		$css = <<<'CSS'
@media (max-width: 999.98px) {
	#header [data-device="mobile"] [data-row="middle"] [data-items="primary"] {
		align-items: center;
		gap: 0.35rem;
	}
	#header [data-device="mobile"] [data-id="trigger"],
	#header [data-device="mobile"] [data-id="search"],
	#header [data-device="mobile"] [data-id="cart"] .ct-cart-item {
		min-width: 44px;
		min-height: 44px;
	}
	#header [data-device="mobile"] .site-branding {
		min-width: 0;
		flex: 1 1 auto;
		max-width: 52vw;
	}
	#header [data-device="mobile"] .site-title {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
}
CSS;

		wp_register_style( 'cttel-blocksy-mobile-header', false, array(), '1.0.0' );
		wp_enqueue_style( 'cttel-blocksy-mobile-header' );
		wp_add_inline_style( 'cttel-blocksy-mobile-header', $css );
	},
	999
);
