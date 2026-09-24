<?php
/**
 * CTTEL mobile storefront — local SVG icons and category placeholders.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Base directory for cttel-ms assets (mu-plugins/assets/cttel-ms). */
function cttel_ms_assets_base_dir(): string {
	return __DIR__ . '/assets/cttel-ms';
}

/**
 * Load an SVG from disk and optionally inject a CSS class on the root element.
 */
function cttel_ms_load_svg( string $relative_path, string $class = '' ): string {
	$path = cttel_ms_assets_base_dir() . '/' . ltrim( $relative_path, '/' );
	if ( ! is_readable( $path ) ) {
		return '';
	}
	$svg = (string) file_get_contents( $path );
	if ( '' === $svg ) {
		return '';
	}
	if ( '' !== $class ) {
		$svg = preg_replace( '/<svg\b/', '<svg class="' . esc_attr( $class ) . '"', $svg, 1 );
	}
	return $svg;
}

/**
 * Map product_cat slug → icon file basename (icons/*.svg).
 */
function cttel_ms_category_icon_key( string $slug ): string {
	$map = array(
		'mobile'              => 'mobile',
		'mobile-phone'          => 'mobile',
		'used-phones'           => 'used-phones',
		'used-phone'            => 'used-phones',
		'used_phones'           => 'used-phones',
		'headphones'            => 'headphones',
		'earphones'             => 'headphones',
		'smartwatch'            => 'smartwatch',
		'smart-watch'           => 'smartwatch',
		'watch'                 => 'smartwatch',
		'accessories'           => 'accessories',
		'accessory'             => 'accessories',
		'gadgets'               => 'gadgets',
		'gadget'                => 'gadgets',
		'mobile-parts'          => 'parts',
		'mobile_parts'          => 'parts',
		'parts'                 => 'parts',
		'laptop'                => 'laptop',
		'tablet'                => 'tablet',
		'uncategorized'         => 'shop',
	);
	return $map[ $slug ] ?? 'shop';
}

/**
 * @param int    $size   Width/height hint for UI icons.
 * @param string $class  Optional CSS class on root SVG.
 */
function cttel_mobile_storefront_icon( string $name, int $size = 24, string $class = 'cttel-ms-svg' ): string {
	$file = cttel_ms_load_svg( 'icons/' . $name . '.svg', $class );
	if ( '' !== $file ) {
		if ( 24 !== $size ) {
			$file = preg_replace( '/\bwidth="[^"]*"/', 'width="' . (int) $size . '"', $file, 1 );
			$file = preg_replace( '/\bheight="[^"]*"/', 'height="' . (int) $size . '"', $file, 1 );
		}
		return $file;
	}
	return cttel_ms_load_svg( 'icons/shop.svg', $class );
}

function cttel_mobile_storefront_category_icon( WP_Term $term ): string {
	$key = cttel_ms_category_icon_key( $term->slug );
	return cttel_mobile_storefront_icon( $key, 28, 'cttel-ms-svg cttel-ms-svg--category' );
}

/**
 * Primary product category slug for imagery (prefers deepest assigned term).
 */
function cttel_ms_product_category_slug( WC_Product $product ): string {
	$terms = get_the_terms( $product->get_id(), 'product_cat' );
	if ( ! is_array( $terms ) || empty( $terms ) ) {
		return 'uncategorized';
	}
	$best     = $terms[0];
	$best_dep = 0;
	foreach ( $terms as $term ) {
		if ( ! $term instanceof WP_Term ) {
			continue;
		}
		if ( 'uncategorized' === $term->slug ) {
			continue;
		}
		$depth = 0;
		$walk  = $term;
		while ( $walk->parent > 0 ) {
			++$depth;
			$parent = get_term( (int) $walk->parent, 'product_cat' );
			if ( ! $parent instanceof WP_Term ) {
				break;
			}
			$walk = $parent;
		}
		if ( $depth >= $best_dep ) {
			$best_dep = $depth;
			$best     = $term;
		}
	}
	return $best->slug;
}

function cttel_ms_placeholder_key_for_slug( string $slug ): string {
	return cttel_ms_category_icon_key( $slug );
}

/** Category card / product card placeholder markup. */
function cttel_ms_category_placeholder_visual( string $slug ): string {
	$key = cttel_ms_placeholder_key_for_slug( $slug );
	$svg = cttel_ms_load_svg( 'placeholders/' . $key . '.svg', 'cttel-ms-placeholder-svg' );
	if ( '' === $svg ) {
		$svg = cttel_ms_load_svg( 'placeholders/shop.svg', 'cttel-ms-placeholder-svg' );
	}
	return '<span class="cttel-ms-visual-placeholder cttel-ms-visual-placeholder--' . esc_attr( $key ) . '" aria-hidden="true">' . $svg . '</span>';
}

function cttel_ms_term_placeholder_visual( WP_Term $term ): string {
	return cttel_ms_category_placeholder_visual( $term->slug );
}

function cttel_ms_product_placeholder_visual( WC_Product $product ): string {
	return cttel_ms_category_placeholder_visual( cttel_ms_product_category_slug( $product ) );
}
