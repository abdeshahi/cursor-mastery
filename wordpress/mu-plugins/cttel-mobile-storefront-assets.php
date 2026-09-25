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

/** Public URL for a file under mu-plugins/assets/cttel-ms/. */
function cttel_ms_asset_url( string $relative_path ): string {
	$relative_path = ltrim( $relative_path, '/' );
	return content_url( 'mu-plugins/assets/cttel-ms/' . $relative_path );
}

/** First attachment ID from WooCommerce product gallery. */
function cttel_ms_product_gallery_attachment_id( WC_Product $product ): int {
	$gallery = $product->get_gallery_image_ids();
	if ( empty( $gallery ) ) {
		return 0;
	}
	return (int) $gallery[0];
}

/**
 * Normalize product name/slug/SKU for token matching (Persian + Latin).
 */
function cttel_ms_normalize_match_text( string $text ): string {
	$text = wp_strip_all_tags( $text );
	$text = mb_strtolower( $text, 'UTF-8' );
	$text = str_replace( array( '‌', 'ي', 'ك', 'ٔ' ), array( ' ', 'ی', 'ک', '' ), $text );
	$text = preg_replace( '/[^\p{L}\p{N}\s\-]+/u', ' ', $text );
	$text = preg_replace( '/\s+/u', ' ', $text );
	return trim( $text );
}

/**
 * Local product photo rules: slug (exact) → file; else substring patterns on normalized haystack.
 *
 * @return array{slug: array<string,string>, patterns: array<int, array{file: string, needles: string[]}>}
 */
function cttel_ms_product_local_photo_rules(): array {
	return array(
		'slug' => array(
			'iphone-15'     => 'products/iphone-15.png',
			'galaxy-s24'    => 'products/galaxy-s24.png',
			'airpods-pro'   => 'products/airpods-pro.png',
			'apple-watch'   => 'products/apple-watch.png',
			'car-charger'   => 'products/car-charger.png',
			'powerbank-20k' => 'products/powerbank-20k.png',
			'bt-headphone'  => 'products/bt-headphone.png',
			'screen-guard'  => 'products/screen-guard.png',
		),
		'sku'  => array(),
		'patterns' => array(
			array(
				'file'    => 'products/iphone-15.png',
				'needles' => array( 'iphone 15', 'iphone-15', 'iphone15', 'آیفون 15', 'ایفون 15' ),
			),
			array(
				'file'    => 'products/galaxy-s24.png',
				'needles' => array( 'galaxy s24', 'galaxy-s24', 's24 ultra', 's24', 'سامسونگ galaxy', 'سامسونگ s24' ),
			),
			array(
				'file'    => 'products/airpods-pro.png',
				'needles' => array( 'airpods pro', 'airpods-pro', 'airpod pro' ),
			),
			array(
				'file'    => 'products/apple-watch.png',
				'needles' => array( 'apple watch', 'apple-watch', 'ساعت apple' ),
			),
			array(
				'file'    => 'products/car-charger.png',
				'needles' => array( 'car charger', 'car-charger', 'شارژر فندکی', 'فندکی' ),
			),
			array(
				'file'    => 'products/powerbank-20k.png',
				'needles' => array( 'powerbank', 'power bank', 'powerbank-20k', 'پاوربانک' ),
			),
			array(
				'file'    => 'products/bt-headphone.png',
				'needles' => array( 'bt-headphone', 'bluetooth headphone', 'هدفون bluetooth', 'هدفون بلوتوث' ),
			),
			array(
				'file'    => 'products/screen-guard.png',
				'needles' => array( 'screen guard', 'screen-guard', 'گلس', 'محافظ صفحه' ),
			),
		),
	);
}

/**
 * Relative path under assets/cttel-ms/ for a matching local product photo, or empty string.
 */
function cttel_ms_product_local_photo_relative_path( WC_Product $product ): string {
	$rules = cttel_ms_product_local_photo_rules();
	$slug  = $product->get_slug();
	if ( isset( $rules['slug'][ $slug ] ) ) {
		return $rules['slug'][ $slug ];
	}
	$sku = $product->get_sku();
	if ( $sku && isset( $rules['sku'][ $sku ] ) ) {
		return $rules['sku'][ $sku ];
	}
	$haystack = cttel_ms_normalize_match_text(
		$product->get_name() . ' ' . $slug . ' ' . $sku
	);
	if ( '' === $haystack ) {
		return '';
	}
	foreach ( $rules['patterns'] as $rule ) {
		foreach ( $rule['needles'] as $needle ) {
			$norm_needle = cttel_ms_normalize_match_text( $needle );
			if ( '' !== $norm_needle && str_contains( $haystack, $norm_needle ) ) {
				return $rule['file'];
			}
		}
	}
	return '';
}

function cttel_ms_product_local_photo_is_readable( string $relative_path ): bool {
	if ( '' === $relative_path ) {
		return false;
	}
	return is_readable( cttel_ms_assets_base_dir() . '/' . ltrim( $relative_path, '/' ) );
}

/**
 * Product card image HTML: featured → gallery → local photo → category placeholder.
 *
 * @param string $img_class CSS class on img element.
 * @param string $size      WordPress image size for attachment IDs.
 */
function cttel_ms_product_card_image_html( WC_Product $product, string $img_class = 'cttel-ms-pcard__img', string $size = 'woocommerce_thumbnail' ): string {
	$alt = $product->get_name();
	$thumb_id = (int) $product->get_image_id();
	if ( $thumb_id > 0 ) {
		$html = wp_get_attachment_image(
			$thumb_id,
			$size,
			false,
			array(
				'class'   => $img_class,
				'loading' => 'lazy',
				'alt'     => $alt,
			)
		);
		if ( $html ) {
			return $html;
		}
	}
	$gallery_id = cttel_ms_product_gallery_attachment_id( $product );
	if ( $gallery_id > 0 ) {
		$html = wp_get_attachment_image(
			$gallery_id,
			$size,
			false,
			array(
				'class'   => $img_class,
				'loading' => 'lazy',
				'alt'     => $alt,
			)
		);
		if ( $html ) {
			return $html;
		}
	}
	$skip_local = apply_filters( 'cttel_ms_skip_local_product_photo', false, $product );
	$local_rel  = cttel_ms_product_local_photo_relative_path( $product );
	if ( ! $skip_local && cttel_ms_product_local_photo_is_readable( $local_rel ) ) {
		return sprintf(
			'<img src="%1$s" class="%2$s" loading="lazy" decoding="async" alt="%3$s" width="400" height="400" />',
			esc_url( cttel_ms_asset_url( $local_rel ) ),
			esc_attr( $img_class ),
			esc_attr( $alt )
		);
	}
	return cttel_ms_product_placeholder_visual( $product );
}
