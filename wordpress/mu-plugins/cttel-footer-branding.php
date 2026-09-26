<?php
/**
 * CTTEL footer — store copyright, compact homepage footer presentation.
 *
 * Does not modify Enamad markup/widgets.
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
		$year = gmdate( 'Y' );
		if ( is_string( $text ) && ( false !== stripos( $text, 'creativethemes' ) || false !== stripos( $text, 'theme_author' ) || false !== stripos( $text, 'قالب وردپرس' ) ) ) {
			$text = '© ' . $year . ' CTTEL.ir';
		}
		if ( function_exists( 'cttel_is_dedicated_homepage' ) && cttel_is_dedicated_homepage() ) {
			return '© ' . $year . ' CTTEL.ir';
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

body.cttel-dedicated-home .ct-footer [data-row="middle"] {
	display: block !important;
	padding-block: 0.65rem 0.5rem !important;
	border-top: 1px solid rgba(11, 31, 58, 0.06);
}

body.cttel-dedicated-home .ct-footer [data-row="middle"] .ct-container {
	gap: 0.75rem 1rem;
}

body.cttel-dedicated-home .ct-footer [data-row="middle"] .widget-title {
	font-size: 0.75rem !important;
	font-weight: 800 !important;
	color: #0b1f3a !important;
	margin-bottom: 0.35rem !important;
}

body.cttel-dedicated-home .ct-footer [data-row="middle"] .widget,
body.cttel-dedicated-home .ct-footer [data-row="middle"] [data-column] {
	font-size: 0.75rem;
	color: #64748b;
	line-height: 1.45;
}

body.cttel-dedicated-home .ct-footer [data-row="middle"] a {
	color: #2563eb;
	font-weight: 600;
	text-decoration: none;
}

body.cttel-dedicated-home .ct-footer [data-id="menu"] ul {
	display: flex;
	flex-wrap: wrap;
	gap: 0.35rem 0.85rem;
	justify-content: center;
	list-style: none;
	margin: 0;
	padding: 0;
}

body.cttel-dedicated-home .ct-footer [data-id="socials"] a {
	opacity: 0.85;
}

body.cttel-dedicated-home .ct-footer-copyright {
	font-size: 0.75rem !important;
	font-weight: 600;
	color: #64748b !important;
	text-align: center;
	line-height: 1.5;
}
CSS;
		wp_register_style( 'cttel-footer-branding', false, array(), '1.1.0' );
		wp_enqueue_style( 'cttel-footer-branding' );
		wp_add_inline_style( 'cttel-footer-branding', $css );
	},
	50
);
