<?php
/**
 * One-time Blocksy audit configuration — run via: wp eval-file blocksy-audit-config.php
 *
 * @package CTTEL
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit( "Run via wp eval-file inside WordPress.\n" );
}

if ( ! function_exists( 'blocksy_manager' ) ) {
	exit( "Blocksy theme is not active.\n" );
}

$vazir = function ( $size = '16px', $weight = 'n4' ) {
	if ( function_exists( 'blocksy_typography_default_values' ) ) {
		return blocksy_typography_default_values(
			array(
				'family'           => 'Vazirmatn',
				'variation'        => $weight,
				'size'             => $size,
				'line-height'      => '1.75',
				'letter-spacing'   => '0em',
				'text-transform'   => 'none',
				'text-decoration'  => 'none',
			)
		);
	}
	return array(
		'family'    => 'Vazirmatn',
		'variation' => $weight,
		'size'      => $size,
	);
};

// --- Typography defaults (editable later in Customizer) ---
set_theme_mod( 'rootTypography', $vazir( '16px', 'n4' ) );
set_theme_mod( 'h1Typography', $vazir( '36px', 'n7' ) );
set_theme_mod( 'h2Typography', $vazir( '30px', 'n7' ) );
set_theme_mod( 'h3Typography', $vazir( '24px', 'n6' ) );
set_theme_mod( 'buttonsTypography', $vazir( '15px', 'n5' ) );

// Menu typography: Customizer → Header → Menu element → Font.

// --- Header: logo, menu, search, account, cart ---
$header = blocksy_manager()->header_builder->get_default_value();

foreach ( $header['sections'] as &$section ) {
	if ( 'type-1' !== $section['id'] ) {
		continue;
	}

	foreach ( $section['desktop'] as &$row ) {
		if ( 'middle-row' !== $row['id'] ) {
			continue;
		}
		foreach ( $row['placements'] as &$placement ) {
			if ( 'end' === $placement['id'] ) {
				$placement['items'] = array( 'menu', 'search', 'account', 'cart' );
			}
		}
	}

	foreach ( $section['mobile'] as &$row ) {
		if ( 'middle-row' === $row['id'] ) {
			foreach ( $row['placements'] as &$placement ) {
				if ( 'end' === $placement['id'] ) {
					$placement['items'] = array( 'cart', 'trigger' );
				}
			}
		}
		if ( 'offcanvas' === $row['id'] ) {
			foreach ( $row['placements'] as &$placement ) {
				if ( 'start' === $placement['id'] ) {
					$placement['items'] = array( 'mobile-menu', 'account' );
				}
			}
		}
	}
}
unset( $section, $row, $placement );

set_theme_mod( 'header_placements', $header );

// --- Footer: contact widget | menu | socials + copyright ---
$footer = blocksy_manager()->footer_builder->get_default_value();

foreach ( $footer['sections'] as &$section ) {
	if ( 'type-1' !== $section['id'] ) {
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
		'copyright_text' => 'Copyright © {current_year} {site_title} — تمامی حقوق محفوظ است.',
	);

	$section['items']['menu'] = array(
		'menu' => 'blocksy_location',
	);

	$section['items']['socials'] = array(
		'footer_socials' => array(
			array(
				'id'      => 'instagram',
				'enabled' => true,
			),
			array(
				'id'      => 'telegram',
				'enabled' => true,
			),
			array(
				'id'      => 'whatsapp',
				'enabled' => true,
			),
		),
	);
}
unset( $section );

set_theme_mod( 'footer_placements', $footer );

// Container width (Customizer → General → Layout).
set_theme_mod( 'maxSiteWidth', '1200px' );

echo "Blocksy audit configuration applied.\n";
