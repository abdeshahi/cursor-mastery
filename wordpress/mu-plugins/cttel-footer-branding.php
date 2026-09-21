<?php
/**
 * CTTEL footer — replace Blocksy/CreativeThemes attribution with store copyright.
 *
 * Does not modify Enamad widgets or footer structure elsewhere.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * @param array<string, mixed>|mixed $footer Blocksy footer_placements theme mod.
 * @return array<string, mixed>|mixed
 */
function cttel_footer_copyright_placements( $footer ) {
	if ( ! is_array( $footer ) || empty( $footer['sections'] ) ) {
		return $footer;
	}

	foreach ( $footer['sections'] as &$section ) {
		if ( empty( $section['items']['copyright'] ) || ! is_array( $section['items']['copyright'] ) ) {
			continue;
		}
		$section['items']['copyright']['copyright_text'] = '© {current_year} CTTEL.ir';
	}
	unset( $section );

	return $footer;
}

add_filter( 'theme_mod_footer_placements', 'cttel_footer_copyright_placements', 25 );

add_filter(
	'blocksy:footer:copyright:default-value',
	static function (): string {
		return '© {current_year} CTTEL.ir';
	}
);

add_filter(
	'blocksy:footer:copyright:value',
	static function ( $text ) {
		if ( is_string( $text ) && ( false !== stripos( $text, 'creativethemes' ) || false !== stripos( $text, 'theme_author' ) || false !== stripos( $text, 'قالب وردپرس' ) ) ) {
			return '© ' . gmdate( 'Y' ) . ' CTTEL.ir';
		}
		return $text;
	},
	20
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		$css = <<<'CSS'
.ct-footer-copyright a[href*="creativethemes.com"] {
	display: none !important;
}
CSS;
		wp_register_style( 'cttel-footer-branding', false, array(), '1.0.1' );
		wp_enqueue_style( 'cttel-footer-branding' );
		wp_add_inline_style( 'cttel-footer-branding', $css );
	},
	50
);
