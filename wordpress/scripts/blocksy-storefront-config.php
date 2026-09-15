<?php
/**
 * CTTEL customer storefront — Blocksy header/footer defaults (Customizer-editable).
 *
 * @package CTTEL
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit( "Run via wp eval-file inside WordPress.\n" );
}

if ( ! function_exists( 'blocksy_manager' ) ) {
	exit( "Blocksy theme is not active.\n" );
}

$installment_url = home_url( '/installment/' );

// --- Header: logo | menu | search | installment CTA | account | cart ---
$header = get_theme_mod( 'header_placements' );
if ( ! is_array( $header ) || empty( $header['sections'] ) ) {
	$header = blocksy_manager()->header_builder->get_default_value();
}

foreach ( $header['sections'] as &$section ) {
	if ( 'type-1' !== ( $section['id'] ?? '' ) ) {
		continue;
	}

	$section['items']['button:cttel-installment'] = array(
		'text'               => 'خرید اقساطی',
		'link'               => $installment_url,
		'link_source'        => 'custom',
		'header_button_type' => 'type-1',
		'visibility'         => array(
			'desktop' => true,
			'tablet'  => true,
			'mobile'  => false,
		),
	);

	foreach ( $section['desktop'] as &$row ) {
		if ( 'middle-row' !== ( $row['id'] ?? '' ) ) {
			continue;
		}
		foreach ( $row['placements'] as &$placement ) {
			if ( 'start' === $placement['id'] && empty( $placement['items'] ) ) {
				$placement['items'] = array( 'logo' );
			}
			if ( 'end' === $placement['id'] ) {
				$placement['items'] = array( 'menu', 'search', 'button:cttel-installment', 'account', 'cart' );
			}
		}
		unset( $placement );
	}
	unset( $row );

	foreach ( $section['mobile'] as &$row ) {
		if ( 'middle-row' === ( $row['id'] ?? '' ) ) {
			foreach ( $row['placements'] as &$placement ) {
				if ( 'start' === $placement['id'] && empty( $placement['items'] ) ) {
					$placement['items'] = array( 'logo' );
				}
				if ( 'end' === $placement['id'] ) {
					$placement['items'] = array( 'search', 'cart', 'trigger' );
				}
			}
			unset( $placement );
		}
		if ( 'offcanvas' === ( $row['id'] ?? '' ) ) {
			foreach ( $row['placements'] as &$placement ) {
				if ( 'start' === $placement['id'] ) {
					$placement['items'] = array( 'mobile-menu', 'button:cttel-installment', 'account' );
				}
			}
			unset( $placement );
		}
	}
	unset( $row );
}
unset( $section );

set_theme_mod( 'header_placements', $header );

// --- Footer ---
$footer = get_theme_mod( 'footer_placements' );
if ( ! is_array( $footer ) || empty( $footer['sections'] ) ) {
	$footer = blocksy_manager()->footer_builder->get_default_value();
}

foreach ( $footer['sections'] as &$section ) {
	if ( 'type-1' !== ( $section['id'] ?? '' ) ) {
		continue;
	}

	$section['rows'] = array(
		array(
			'id'      => 'middle-row',
			'columns' => array(
				array( 'widget-area-1' ),
				array( 'menu' ),
				array( 'socials' ),
			),
		),
		array(
			'id'      => 'bottom-row',
			'columns' => array(
				array( 'copyright' ),
			),
		),
	);

	$section['items']['copyright'] = array(
		'copyright_text' => '© {current_year} {site_title} — تمامی حقوق محفوظ است.',
	);

	$section['items']['menu'] = array(
		'menu' => 'blocksy_location',
	);

	$section['items']['socials'] = array(
		'footer_socials' => array(
			array( 'id' => 'instagram', 'enabled' => true ),
			array( 'id' => 'telegram', 'enabled' => true ),
			array( 'id' => 'whatsapp', 'enabled' => true ),
		),
	);
}
unset( $section );

set_theme_mod( 'footer_placements', $footer );

// Layout & sticky header (editable in Customizer).
set_theme_mod( 'maxSiteWidth', '1200px' );
set_theme_mod( 'enable_sticky_header', 'yes' );

delete_transient( 'blocksy_dynamic_styles_descriptor' );

echo "CTTEL customer storefront Blocksy config applied.\n";
