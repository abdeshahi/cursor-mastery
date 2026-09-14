<?php
/**
 * CTTEL Quick Categories — sync homepage cards with WooCommerce product categories.
 *
 * Shortcode: [cttel_quick_categories]
 * Source of truth: Products → Categories (name, slug, thumbnail, description).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * Category card configuration (slug => fallback emoji).
 * Order defines grid layout (3 + 3).
 */
function cttel_quick_category_map(): array {
	return array(
		array(
			'type'     => 'category',
			'slug'     => 'mobile',
			'fallback' => '📱',
		),
		array(
			'type'     => 'category',
			'slug'     => 'headphones',
			'fallback' => '🎧',
		),
		array(
			'type'     => 'category',
			'slug'     => 'smartwatch',
			'fallback' => '⌚',
		),
		array(
			'type'     => 'category',
			'slug'     => 'accessories',
			'fallback' => '🔌',
		),
		array(
			'type'     => 'category',
			'slug'     => 'gadgets',
			'fallback' => '💡',
		),
		array(
			'type'     => 'link',
			'url'      => home_url( '/installment/' ),
			'name'     => 'خرید اقساطی',
			'fallback' => '💳',
			'bg'       => '#eff6ff',
		),
	);
}

/**
 * Render icon or WooCommerce category thumbnail.
 */
function cttel_quick_category_visual( WP_Term $term, string $fallback ): string {
	$thumb_id = (int) get_term_meta( $term->term_id, 'thumbnail_id', true );

	if ( $thumb_id > 0 ) {
		$img = wp_get_attachment_image(
			$thumb_id,
			'woocommerce_thumbnail',
			false,
			array(
				'class'   => 'cttel-quick-cat-thumb',
				'loading' => 'lazy',
				'alt'     => esc_attr( $term->name ),
				'style'   => 'width:48px;height:48px;object-fit:cover;border-radius:8px;display:block;margin:0 auto;',
			)
		);
		if ( $img ) {
			return '<div class="cttel-quick-cat-visual has-text-align-center">' . $img . '</div>';
		}
	}

	return '<p class="has-text-align-center" style="font-size:1.75rem">' . esc_html( $fallback ) . '</p>';
}

/**
 * Render a single category card matching existing Blocksy/Gutenberg markup.
 */
function cttel_quick_category_card( array $item ): string {
	$bg      = $item['bg'] ?? '#ffffff';
	$wrapper = sprintf(
		'<div class="wp-block-group has-border-color has-tertiary-border-color has-background" style="border-width:1px;border-radius:12px;background-color:%s;padding-top:1rem;padding-right:0.75rem;padding-bottom:1rem;padding-left:0.75rem">',
		esc_attr( $bg )
	);

	if ( 'link' === ( $item['type'] ?? 'category' ) ) {
		$visual = '<p class="has-text-align-center" style="font-size:1.75rem">' . esc_html( $item['fallback'] ) . '</p>';
		$title  = sprintf(
			'<h3 class="wp-block-heading has-text-align-center" style="font-size:1rem"><a href="%s">%s</a></h3>',
			esc_url( $item['url'] ),
			esc_html( $item['name'] )
		);
		return $wrapper . $visual . $title . '</div>';
	}

	$term = get_term_by( 'slug', $item['slug'], 'product_cat' );
	if ( ! $term instanceof WP_Term ) {
		return '';
	}

	$url         = get_term_link( $term );
	$visual      = cttel_quick_category_visual( $term, $item['fallback'] );
	$description = trim( wp_strip_all_tags( $term->description ) );

	$subtitle = '';
	if ( '' !== $description ) {
		$subtitle = sprintf(
			'<p class="has-text-align-center cttel-quick-cat-sub" style="font-size:0.75rem;line-height:1.4;margin:0.35rem 0 0;opacity:0.75">%s</p>',
			esc_html( wp_trim_words( $description, 8, '…' ) )
		);
	}

	$title = sprintf(
		'<h3 class="wp-block-heading has-text-align-center" style="font-size:1rem"><a href="%s">%s</a></h3>',
		esc_url( $url ),
		esc_html( $term->name )
	);

	return $wrapper . $visual . $title . $subtitle . '</div>';
}

/**
 * Render quick categories grid (2 rows × 3 columns).
 */
function cttel_render_quick_categories(): string {
	$items = cttel_quick_category_map();
	$rows  = array_chunk( $items, 3 );
	$html  = '';

	foreach ( $rows as $index => $row ) {
		$style = 0 === $index ? '' : ' style="margin-top:0.75rem"';
		$html .= '<div class="wp-block-columns"' . $style . '>';

		foreach ( $row as $item ) {
			$card = cttel_quick_category_card( $item );
			$html .= '<div class="wp-block-column">';
			$html .= $card ?: '';
			$html .= '</div>';
		}

		$html .= '</div>';
	}

	return $html;
}

add_shortcode( 'cttel_quick_categories', 'cttel_render_quick_categories' );
