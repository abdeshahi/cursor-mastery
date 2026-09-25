<?php
/**
 * Product search — Persian-friendly, SKU + model terms, mobile results UI.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * Normalize Persian/Arabic digits to ASCII for matching.
 */
function cttel_search_normalize_digits( string $text ): string {
	$persian = array( '۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹' );
	$arabic  = array( '٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩' );
	$latin   = array( '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' );
	$text    = str_replace( $persian, $latin, $text );
	return str_replace( $arabic, $latin, $text );
}

function cttel_ms_is_product_search(): bool {
	return is_search() && ( ! isset( $_GET['post_type'] ) || 'product' === (string) wp_unslash( $_GET['post_type'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
}

add_action(
	'pre_get_posts',
	static function ( WP_Query $query ): void {
		if ( is_admin() || ! $query->is_main_query() || ! $query->is_search() ) {
			return;
		}
		$query->set( 'post_type', 'product' );
		$raw = $query->get( 's' );
		if ( is_string( $raw ) && $raw !== cttel_search_normalize_digits( $raw ) ) {
			$query->set( 's', cttel_search_normalize_digits( $raw ) );
		}
	},
	5
);

add_filter(
	'posts_join',
	static function ( string $join, WP_Query $query ): string {
		if ( is_admin() || ! $query->is_main_query() || ! $query->is_search() ) {
			return $join;
		}
		global $wpdb;
		if ( ! str_contains( $join, 'cttel_search_meta' ) ) {
			$join .= " LEFT JOIN {$wpdb->postmeta} AS cttel_search_meta ON ({$wpdb->posts}.ID = cttel_search_meta.post_id AND cttel_search_meta.meta_key = '_sku') ";
		}
		return $join;
	},
	10,
	2
);

add_filter(
	'posts_search',
	static function ( string $search, WP_Query $query ): string {
		if ( is_admin() || ! $query->is_main_query() || ! $query->is_search() || '' === $search ) {
			return $search;
		}
		global $wpdb;
		$term = $query->get( 's' );
		if ( ! is_string( $term ) || '' === trim( $term ) ) {
			return $search;
		}
		$like = '%' . $wpdb->esc_like( $term ) . '%';
		$search = preg_replace( '/\)\s*$/', '', $search ) ?? $search;
		$search .= $wpdb->prepare( " OR (cttel_search_meta.meta_value LIKE %s)", $like ); // phpcs:ignore WordPress.DB.PreparedSQLPlaceholders
		$search .= ')';

		$term_ids = array_merge(
			cttel_search_matching_model_term_ids( $term ),
			cttel_search_matching_category_term_ids( $term )
		);
		$term_ids = array_values( array_unique( array_filter( array_map( 'intval', $term_ids ) ) ) );
		if ( ! empty( $term_ids ) ) {
			$ids_sql = implode( ',', $term_ids );
			$search  = preg_replace( '/\)\s*$/', '', $search ) ?? $search;
			$search .= " OR ({$wpdb->posts}.ID IN (SELECT object_id FROM {$wpdb->term_relationships} WHERE term_taxonomy_id IN (SELECT term_taxonomy_id FROM {$wpdb->term_taxonomy} WHERE term_id IN ({$ids_sql})))) )";
		}
		return $search;
	},
	10,
	2
);

/**
 * @return int[]
 */
/**
 * @return int[]
 */
function cttel_search_matching_category_term_ids( string $term ): array {
	$found = get_terms(
		array(
			'taxonomy'   => 'product_cat',
			'hide_empty' => true,
			'search'     => $term,
			'number'     => 8,
		)
	);
	if ( is_wp_error( $found ) || empty( $found ) ) {
		return array();
	}
	return array_map(
		static function ( $t ) {
			return $t instanceof WP_Term ? (int) $t->term_id : 0;
		},
		$found
	);
}

/**
 * @return int[]
 */
function cttel_search_matching_model_term_ids( string $term ): array {
	if ( ! taxonomy_exists( 'cttel_device_model' ) ) {
		return array();
	}
	$found = get_terms(
		array(
			'taxonomy'   => 'cttel_device_model',
			'hide_empty' => false,
			'search'     => $term,
			'number'     => 10,
		)
	);
	if ( is_wp_error( $found ) || empty( $found ) ) {
		return array();
	}
	return array_map(
		static function ( $t ) {
			return $t instanceof WP_Term ? (int) $t->term_id : 0;
		},
		$found
	);
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_ms_is_product_search() ) {
			$classes[] = 'cttel-ms-search-results';
		}
		return $classes;
	}
);

add_action(
	'woocommerce_before_main_content',
	static function (): void {
		if ( ! cttel_ms_is_product_search() || ! function_exists( 'cttel_mobile_storefront_uses_shell' ) || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		echo '<main class="cttel-ms-main cttel-ms-main--search" id="cttel-ms-search-main">';
		$query = get_search_query();
		?>
		<div class="cttel-ms-search-head">
			<h1 class="cttel-ms-search-head__title"><?php esc_html_e( 'نتایج جستجو', 'cttel-store' ); ?></h1>
			<?php if ( $query ) : ?>
				<p class="cttel-ms-search-head__query"><?php echo esc_html( $query ); ?></p>
			<?php endif; ?>
			<div class="cttel-ms-search-head__form">
				<?php cttel_mobile_storefront_product_search_form(); ?>
			</div>
		</div>
		<?php
	},
	4
);

add_action(
	'woocommerce_after_main_content',
	static function (): void {
		if ( ! cttel_ms_is_product_search() || ! function_exists( 'cttel_mobile_storefront_uses_shell' ) || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		echo '</main>';
	},
	50
);

add_filter(
	'woocommerce_product_loop_start',
	static function ( string $html ): string {
		if ( ! cttel_ms_is_product_search() ) {
			return $html;
		}
		return preg_replace(
			'/class="([^"]*products[^"]*)"/',
			'class="$1 cttel-ms-products__grid cttel-ms-products__grid--search"',
			$html,
			1
		) ?? $html;
	}
);
