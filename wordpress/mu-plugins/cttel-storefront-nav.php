<?php
/**
 * CTTEL storefront navigation — remove demo clutter from public menus (presentation only).
 *
 * Does not modify mobile off-canvas mechanics or header builder structure.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * Drop auto-generated demo / English-only clutter from primary menus.
 *
 * @param WP_Post[] $items Menu items.
 * @return WP_Post[]
 */
function cttel_storefront_filter_nav_items( array $items ): array {
	$hide_slugs = array(
		'sample-page',
		'privacy-policy',
	);

	$hide_titles = array(
		'sample page',
		'cart',
		'checkout',
		'my account',
		'shop',
	);

	$out = array();
	foreach ( $items as $item ) {
		if ( ! $item instanceof WP_Post ) {
			continue;
		}
		$slug = '';
		if ( 'page' === $item->object && ! empty( $item->object_id ) ) {
			$page = get_post( (int) $item->object_id );
			if ( $page instanceof WP_Post ) {
				$slug = $page->post_name;
			}
		}
		if ( $slug && in_array( $slug, $hide_slugs, true ) ) {
			continue;
		}
		$title = strtolower( trim( wp_strip_all_tags( $item->title ) ) );
		if ( in_array( $title, $hide_titles, true ) ) {
			continue;
		}
		$url = (string) $item->url;
		if ( preg_match( '#/(cart|checkout|my-account|sample-page)(/|$)#i', $url ) ) {
			continue;
		}
		$out[] = $item;
	}
	return $out;
}

add_filter(
	'wp_nav_menu_objects',
	static function ( $items, $args ) {
		if ( ! is_front_page() || empty( $items ) || ! is_array( $items ) ) {
			return $items;
		}
		if ( ! empty( $args->theme_location ) && false !== strpos( (string) $args->theme_location, 'footer' ) ) {
			return $items;
		}
		return cttel_storefront_filter_nav_items( $items );
	},
	20,
	2
);
