<?php
/**
 * CTTEL catalog — categories, used phones, compatibility, filters (WooCommerce-native).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

const CTTEL_CATALOG_VERSION     = '1.0.0';
const CTTEL_CATALOG_BOOT_KEY      = 'cttel_catalog_structure_version';
const CTTEL_DEVICE_MODEL_TAX      = 'cttel_device_model';
const CTTEL_META_CONDITION        = '_cttel_condition';
const CTTEL_META_USED_SPECS       = '_cttel_used_specs';
const CTTEL_OPTION_INSTALLMENT           = 'cttel_installment_page_html';
const CTTEL_OPTION_INSTALLMENT_LEAD_URL  = 'cttel_installment_consultation_url';
const CTTEL_OPTION_INSTALLMENT_LEAD_LBL  = 'cttel_installment_consultation_label';

/**
 * @return array<string, string>
 */
function cttel_catalog_used_spec_field_labels(): array {
	return array(
		'status'           => __( 'وضعیت', 'cttel-store' ),
		'brand'            => __( 'برند', 'cttel-store' ),
		'model'            => __( 'مدل', 'cttel-store' ),
		'storage'          => __( 'حافظه', 'cttel-store' ),
		'color'            => __( 'رنگ', 'cttel-store' ),
		'cosmetic'         => __( 'وضعیت ظاهری', 'cttel-store' ),
		'battery_health'   => __( 'سلامت باتری', 'cttel-store' ),
		'repair_status'    => __( 'وضعیت تعمیرشدگی', 'cttel-store' ),
		'parts_replaced'   => __( 'وضعیت تعویض قطعه', 'cttel-store' ),
		'screen_status'    => __( 'وضعیت صفحه‌نمایش', 'cttel-store' ),
		'biometric_status' => __( 'وضعیت Face ID / Touch ID', 'cttel-store' ),
		'camera_status'    => __( 'وضعیت دوربین', 'cttel-store' ),
		'audio_status'     => __( 'وضعیت اسپیکر و میکروفن', 'cttel-store' ),
		'charging_status'  => __( 'وضعیت شارژ', 'cttel-store' ),
		'registry'         => __( 'رجیستری', 'cttel-store' ),
		'accessories'      => __( 'لوازم همراه', 'cttel-store' ),
		'warranty'         => __( 'مهلت تست / ضمانت', 'cttel-store' ),
		'notes'            => __( 'توضیحات', 'cttel-store' ),
	);
}

/**
 * @return bool
 */
function cttel_is_staging_catalog_site(): bool {
	if ( function_exists( 'cttel_is_staging_site' ) ) {
		return cttel_is_staging_site();
	}
	$host = isset( $_SERVER['HTTP_HOST'] ) ? strtolower( (string) $_SERVER['HTTP_HOST'] ) : '';
	return str_contains( $host, 'staging.' ) || str_contains( $host, 'staging.cttel' );
}

add_action(
	'init',
	static function (): void {
		register_taxonomy(
			CTTEL_DEVICE_MODEL_TAX,
			'product',
			array(
				'labels'            => array(
					'name'          => __( 'مدل دستگاه', 'cttel-store' ),
					'singular_name' => __( 'مدل دستگاه', 'cttel-store' ),
				),
				'public'            => false,
				'show_ui'           => true,
				'show_admin_column' => true,
				'show_in_rest'      => true,
				'hierarchical'      => false,
				'rewrite'           => false,
			)
		);
	},
	12
);

/**
 * @return array<string, array{children: string[]}>
 */
function cttel_catalog_category_tree(): array {
	return array(
		'mobile'       => array(
			'name'     => 'موبایل',
			'children' => array(
				'mobile-new'  => 'گوشی نو',
				'mobile-used' => 'گوشی کارکرده',
			),
		),
		'accessories'  => array(
			'name'     => 'لوازم جانبی',
			'children' => array(
				'acc-case'     => 'قاب و کاور',
				'acc-glass'    => 'گلس و محافظ صفحه',
				'acc-charger'  => 'شارژر',
				'acc-cable'    => 'کابل',
				'acc-powerbank' => 'پاوربانک',
				'acc-headphone' => 'هندزفری و هدفون',
				'acc-other'    => 'سایر لوازم جانبی',
			),
		),
		'gadget'       => array(
			'name'     => 'گجت',
			'children' => array(
				'gadget-watch'    => 'ساعت هوشمند',
				'gadget-earbuds'  => 'هندزفری بی‌سیم',
				'gadget-speaker'  => 'اسپیکر',
				'gadget-other'    => 'گجت‌های دیگر',
			),
		),
	);
}

/**
 * Ensure global attributes exist (brand, storage).
 */
function cttel_catalog_ensure_attributes(): void {
	if ( ! function_exists( 'wc_create_attribute' ) || ! function_exists( 'wc_get_attribute_taxonomies' ) ) {
		return;
	}
	$existing = wp_list_pluck( wc_get_attribute_taxonomies(), 'attribute_name' );
	$defs     = array(
		'brand'   => 'برند',
		'storage' => 'حافظه',
	);
	foreach ( $defs as $slug => $label ) {
		if ( in_array( $slug, $existing, true ) ) {
			continue;
		}
		$id = wc_create_attribute(
			array(
				'name'         => $label,
				'slug'         => $slug,
				'type'         => 'select',
				'order_by'     => 'menu_order',
				'has_archives' => false,
			)
		);
		if ( is_wp_error( $id ) ) {
			continue;
		}
		register_taxonomy(
			wc_attribute_taxonomy_name( $slug ),
			'product',
			array(
				'labels'       => array( 'name' => $label ),
				'hierarchical' => false,
				'show_ui'      => false,
				'query_var'    => true,
				'rewrite'      => false,
			)
		);
	}
}

/**
 * Create category tree (staging bootstrap + safe idempotent elsewhere).
 */
function cttel_catalog_bootstrap_structure(): void {
	if ( ! taxonomy_exists( 'product_cat' ) ) {
		return;
	}
	cttel_catalog_ensure_attributes();
	$order = 0;
	foreach ( cttel_catalog_category_tree() as $parent_slug => $parent_def ) {
		++$order;
		$parent = term_exists( $parent_slug, 'product_cat' );
		if ( ! $parent ) {
			$insert = wp_insert_term(
				$parent_def['name'],
				'product_cat',
				array(
					'slug' => $parent_slug,
				)
			);
			if ( is_wp_error( $insert ) ) {
				continue;
			}
			$parent_id = (int) $insert['term_id'];
		} else {
			$parent_id = (int) ( is_array( $parent ) ? $parent['term_id'] : $parent );
		}
		update_term_meta( $parent_id, 'order', $order );
		$child_order = 0;
		foreach ( $parent_def['children'] as $child_slug => $child_name ) {
			++$child_order;
			$child = term_exists( $child_slug, 'product_cat' );
			if ( ! $child ) {
				$insert = wp_insert_term(
					$child_name,
					'product_cat',
					array(
						'slug'   => $child_slug,
						'parent' => $parent_id,
					)
				);
				if ( is_wp_error( $insert ) ) {
					continue;
				}
				$child_id = (int) $insert['term_id'];
			} else {
				$child_id = (int) ( is_array( $child ) ? $child['term_id'] : $child );
				wp_update_term(
					$child_id,
					'product_cat',
					array(
						'parent' => $parent_id,
						'name'     => $child_name,
					)
				);
			}
			update_term_meta( $child_id, 'order', $child_order );
		}
	}
}

add_action(
	'init',
	static function (): void {
		if ( ! cttel_is_staging_catalog_site() ) {
			return;
		}
		$applied = get_option( CTTEL_CATALOG_BOOT_KEY, '' );
		if ( CTTEL_CATALOG_VERSION === $applied ) {
			return;
		}
		cttel_catalog_bootstrap_structure();
		cttel_catalog_staging_sample_assignments();
		cttel_catalog_staging_create_used_sample();
		update_option( CTTEL_CATALOG_BOOT_KEY, CTTEL_CATALOG_VERSION );
	},
	30
);

/**
 * Assign a few existing staging products + one used sample (no fake catalog flood).
 */
function cttel_catalog_staging_sample_assignments(): void {
	$map = array(
		'iphone-15'     => array( 'mobile-new', 'cttel_device_model' => 'iphone-15' ),
		'galaxy-s24'    => array( 'mobile-new' ),
		'powerbank-20k' => array( 'acc-powerbank' ),
		'airpods-pro'   => array( 'gadget-earbuds' ),
	);
	foreach ( $map as $slug => $conf ) {
		$product_id = cttel_catalog_product_id_by_slug( $slug );
		if ( ! $product_id ) {
			continue;
		}
		$cat_slug = $conf[0];
		$term     = get_term_by( 'slug', $cat_slug, 'product_cat' );
		if ( $term instanceof WP_Term ) {
			wp_set_object_terms( $product_id, array( (int) $term->term_id ), 'product_cat', true );
		}
		if ( ! empty( $conf['cttel_device_model'] ) ) {
			wp_set_object_terms( $product_id, array( $conf['cttel_device_model'] ), CTTEL_DEVICE_MODEL_TAX, false );
		}
		update_post_meta( $product_id, CTTEL_META_CONDITION, 'new' );
	}

	$iphone = cttel_catalog_product_id_by_slug( 'iphone-15' );
	if ( $iphone ) {
		wp_set_object_terms( $iphone, array( 'iphone-15' ), CTTEL_DEVICE_MODEL_TAX, false );
	}
	if ( cttel_catalog_product_id_by_slug( 'powerbank-20k' ) ) {
		wp_set_object_terms( cttel_catalog_product_id_by_slug( 'powerbank-20k' ), array( 'iphone-15' ), CTTEL_DEVICE_MODEL_TAX, false );
	}
}

/**
 * One staging used-phone sample (only if category empty).
 */
function cttel_catalog_staging_create_used_sample(): void {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return;
	}
	$existing = wc_get_products(
		array(
			'limit'    => 1,
			'status'   => 'publish',
			'category' => array( 'mobile-used' ),
		)
	);
	if ( ! empty( $existing ) ) {
		return;
	}
	$product = new WC_Product_Simple();
	$product->set_name( 'آیفون 13 — کارکرده (نمونه استیجینگ)' );
	$product->set_status( 'publish' );
	$product->set_regular_price( '28500000' );
	$product->set_stock_status( 'instock' );
	$product->set_catalog_visibility( 'visible' );
	$product->set_sku( 'CTTEL-USED-SAMPLE-1' );
	$id = $product->save();
	if ( ! $id ) {
		return;
	}
	wp_set_object_terms( $id, array( 'mobile-used' ), 'product_cat', false );
	wp_set_object_terms( $id, array( 'iphone-13-sample' ), CTTEL_DEVICE_MODEL_TAX, false );
	update_post_meta( $id, CTTEL_META_CONDITION, 'used' );
	update_post_meta(
		$id,
		CTTEL_META_USED_SPECS,
		array(
			'status'         => 'کارکرده',
			'brand'          => 'Apple',
			'model'          => 'iPhone 13',
			'storage'        => '128GB',
			'cosmetic'       => 'خط و خش جزئی',
			'battery_health' => '87%',
			'registry'       => 'فعال',
			'warranty'       => '۷ روز مهلت تست فروشگاه',
			'notes'          => 'نمونه QA استیجینگ — تصاویر واقعی را در گالری بارگذاری کنید.',
		)
	);
}

/**
 * @return int Product ID or 0.
 */
function cttel_catalog_product_id_by_slug( string $slug ): int {
	$post = get_page_by_path( $slug, OBJECT, 'product' );
	return $post instanceof WP_Post ? (int) $post->ID : 0;
}

/**
 * @param WC_Product|int|null $product Product or ID.
 */
function cttel_product_is_used( $product ): bool {
	$product = is_numeric( $product ) ? wc_get_product( (int) $product ) : $product;
	if ( ! $product instanceof WC_Product ) {
		return false;
	}
	if ( 'used' === (string) $product->get_meta( CTTEL_META_CONDITION ) ) {
		return true;
	}
	if ( has_term( 'mobile-used', 'product_cat', $product->get_id() ) ) {
		return true;
	}
	return false;
}

/**
 * @param int|WC_Product $product
 */
function cttel_product_is_new( $product ): bool {
	if ( cttel_product_is_used( $product ) ) {
		return false;
	}
	$product = is_numeric( $product ) ? wc_get_product( (int) $product ) : $product;
	if ( ! $product instanceof WC_Product ) {
		return false;
	}
	if ( 'new' === (string) $product->get_meta( CTTEL_META_CONDITION ) ) {
		return true;
	}
	return has_term( 'mobile-new', 'product_cat', $product->get_id() );
}

/**
 * @return array<string, string>
 */
function cttel_product_used_specs( WC_Product $product ): array {
	$raw = $product->get_meta( CTTEL_META_USED_SPECS, true );
	if ( ! is_array( $raw ) ) {
		return array();
	}
	$labels = cttel_catalog_used_spec_field_labels();
	$out    = array();
	foreach ( $labels as $key => $label ) {
		if ( empty( $raw[ $key ] ) || ! is_string( $raw[ $key ] ) ) {
			continue;
		}
		$value = trim( $raw[ $key ] );
		if ( '' === $value ) {
			continue;
		}
		$out[ $label ] = $value;
	}
	return $out;
}

add_filter(
	'cttel_ms_skip_local_product_photo',
	static function ( bool $skip, WC_Product $product ): bool {
		if ( cttel_product_is_used( $product ) ) {
			return true;
		}
		return $skip;
	},
	10,
	2
);

/** Admin — used phone fields. */
add_action(
	'woocommerce_product_options_general_product_data',
	static function (): void {
		global $post;
		if ( ! $post instanceof WP_Post ) {
			return;
		}
		echo '<div class="options_group cttel-used-specs-panel">';
		woocommerce_wp_select(
			array(
				'id'          => CTTEL_META_CONDITION,
				'label'       => __( 'نوع کالا', 'cttel-store' ),
				'options'     => array(
					''     => __( '—', 'cttel-store' ),
					'new'  => __( 'نو', 'cttel-store' ),
					'used' => __( 'کارکرده', 'cttel-store' ),
				),
				'value'       => (string) get_post_meta( $post->ID, CTTEL_META_CONDITION, true ),
				'desc_tip'    => true,
				'description' => __( 'برای گوشی کارکرده، مشخصات زیر را تکمیل کنید. تصاویر واقعی دستگاه را در گالری محصول بارگذاری کنید.', 'cttel-store' ),
			)
		);
		$specs = get_post_meta( $post->ID, CTTEL_META_USED_SPECS, true );
		if ( ! is_array( $specs ) ) {
			$specs = array();
		}
		foreach ( cttel_catalog_used_spec_field_labels() as $key => $label ) {
			woocommerce_wp_textarea_input(
				array(
					'id'          => 'cttel_used_spec_' . $key,
					'label'       => $label,
					'value'       => isset( $specs[ $key ] ) ? (string) $specs[ $key ] : '',
					'placeholder' => '',
					'rows'        => 2,
				)
			);
		}
		echo '</div>';
	}
);

add_action(
	'woocommerce_admin_process_product_object',
	static function ( WC_Product $product ): void {
		if ( isset( $_POST[ CTTEL_META_CONDITION ] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
			$condition = sanitize_key( wp_unslash( (string) $_POST[ CTTEL_META_CONDITION ] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Missing
			if ( in_array( $condition, array( 'new', 'used' ), true ) ) {
				$product->update_meta_data( CTTEL_META_CONDITION, $condition );
			} else {
				$product->delete_meta_data( CTTEL_META_CONDITION );
			}
		}
		$specs = array();
		foreach ( array_keys( cttel_catalog_used_spec_field_labels() ) as $key ) {
			$field = 'cttel_used_spec_' . $key;
			if ( ! isset( $_POST[ $field ] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
				continue;
			}
			$value = sanitize_textarea_field( wp_unslash( (string) $_POST[ $field ] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Missing
			if ( '' !== $value ) {
				$specs[ $key ] = $value;
			}
		}
		if ( ! empty( $specs ) ) {
			$product->update_meta_data( CTTEL_META_USED_SPECS, $specs );
		} else {
			$product->delete_meta_data( CTTEL_META_USED_SPECS );
		}
	}
);

/** PDP — used spec card (before add to cart). */
add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		global $product;
		if ( ! $product instanceof WC_Product || ! cttel_product_is_used( $product ) ) {
			return;
		}
		$specs = cttel_product_used_specs( $product );
		if ( empty( $specs ) ) {
			return;
		}
		echo '<section class="cttel-ms-used-specs" aria-labelledby="cttel-used-specs-title">';
		echo '<h2 id="cttel-used-specs-title" class="cttel-ms-used-specs__title">' . esc_html__( 'مشخصات گوشی کارکرده', 'cttel-store' ) . '</h2>';
		echo '<dl class="cttel-ms-used-specs__list">';
		foreach ( $specs as $label => $value ) {
			echo '<div class="cttel-ms-used-specs__row"><dt>' . esc_html( $label ) . '</dt><dd>' . esc_html( $value ) . '</dd></div>';
		}
		echo '</dl></section>';
	},
	22
);

/** PDP — accessory model chips near price. */
add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		global $product;
		if ( ! $product instanceof WC_Product || ! cttel_catalog_product_in_accessories_tree( $product->get_id() ) ) {
			return;
		}
		$model_terms = wp_get_post_terms( $product->get_id(), CTTEL_DEVICE_MODEL_TAX );
		if ( is_wp_error( $model_terms ) || empty( $model_terms ) ) {
			return;
		}
		echo '<section class="cttel-ms-compat cttel-ms-compat--models cttel-ms-compat--summary" aria-labelledby="cttel-compat-models-title">';
		echo '<h2 id="cttel-compat-models-title" class="cttel-ms-compat__title">' . esc_html__( 'مناسب برای', 'cttel-store' ) . '</h2>';
		echo '<ul class="cttel-ms-compat__chips">';
		foreach ( $model_terms as $term ) {
			if ( ! $term instanceof WP_Term ) {
				continue;
			}
			echo '<li class="cttel-ms-compat__chip">' . esc_html( $term->name ) . '</li>';
		}
		echo '</ul></section>';
	},
	13
);

/** PDP — related compatibility blocks (below purchase area). */
add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		$accessories = cttel_catalog_compatible_accessories( $product, 6 );
		if ( ! empty( $accessories ) ) {
			echo '<section class="cttel-ms-compat" aria-labelledby="cttel-compat-title">';
			echo '<h2 id="cttel-compat-title" class="cttel-ms-compat__title">' . esc_html__( 'لوازم جانبی پیشنهادی', 'cttel-store' ) . '</h2>';
			echo '<ul class="cttel-ms-compat__list">';
			foreach ( $accessories as $acc ) {
				if ( ! $acc instanceof WC_Product ) {
					continue;
				}
				echo '<li><a href="' . esc_url( $acc->get_permalink() ) . '">' . esc_html( $acc->get_name() ) . '</a></li>';
			}
			echo '</ul></section>';
		}
		$phones = cttel_catalog_compatible_for_accessory( $product, 4 );
		if ( ! empty( $phones ) ) {
			echo '<section class="cttel-ms-compat" aria-labelledby="cttel-compat-phones-title">';
			echo '<h2 id="cttel-compat-phones-title" class="cttel-ms-compat__title">' . esc_html__( 'گوشی‌های مرتبط', 'cttel-store' ) . '</h2>';
			echo '<ul class="cttel-ms-compat__list">';
			foreach ( $phones as $phone ) {
				if ( ! $phone instanceof WC_Product ) {
					continue;
				}
				echo '<li><a href="' . esc_url( $phone->get_permalink() ) . '">' . esc_html( $phone->get_name() ) . '</a></li>';
			}
			echo '</ul></section>';
		}
	},
	55
);

/**
 * @return WC_Product[]
 */
function cttel_catalog_compatible_accessories( WC_Product $product, int $limit = 6 ): array {
	$terms = wp_get_post_terms( $product->get_id(), CTTEL_DEVICE_MODEL_TAX, array( 'fields' => 'ids' ) );
	if ( is_wp_error( $terms ) || empty( $terms ) ) {
		return array();
	}
	$acc_parent = get_term_by( 'slug', 'accessories', 'product_cat' );
	if ( ! $acc_parent instanceof WP_Term ) {
		return array();
	}
	$query = new WP_Query(
		array(
			'post_type'      => 'product',
			'post_status'    => 'publish',
			'posts_per_page' => $limit,
			'post__not_in'   => array( $product->get_id() ),
			'tax_query'      => array(
				'relation' => 'AND',
				array(
					'taxonomy' => CTTEL_DEVICE_MODEL_TAX,
					'field'    => 'term_id',
					'terms'    => $terms,
				),
				array(
					'taxonomy'         => 'product_cat',
					'field'            => 'term_id',
					'terms'            => array( (int) $acc_parent->term_id ),
					'include_children' => true,
				),
			),
		)
	);
	$out = array();
	foreach ( $query->posts as $post ) {
		$p = wc_get_product( $post );
		if ( $p instanceof WC_Product ) {
			$out[] = $p;
		}
	}
	return $out;
}

/**
 * @return WC_Product[]
 */
function cttel_catalog_product_in_accessories_tree( int $product_id ): bool {
	$root = get_term_by( 'slug', 'accessories', 'product_cat' );
	if ( ! $root instanceof WP_Term ) {
		return false;
	}
	$terms = get_the_terms( $product_id, 'product_cat' );
	if ( ! is_array( $terms ) ) {
		return false;
	}
	foreach ( $terms as $term ) {
		if ( ! $term instanceof WP_Term ) {
			continue;
		}
		if ( (int) $term->term_id === (int) $root->term_id ) {
			return true;
		}
		$ancestors = get_ancestors( (int) $term->term_id, 'product_cat' );
		if ( in_array( (int) $root->term_id, array_map( 'intval', $ancestors ), true ) ) {
			return true;
		}
	}
	return false;
}

/**
 * @return WC_Product[]
 */
function cttel_catalog_compatible_for_accessory( WC_Product $product, int $limit = 4 ): array {
	if ( ! cttel_catalog_product_in_accessories_tree( $product->get_id() ) ) {
		return array();
	}
	$terms = wp_get_post_terms( $product->get_id(), CTTEL_DEVICE_MODEL_TAX, array( 'fields' => 'ids' ) );
	if ( is_wp_error( $terms ) || empty( $terms ) ) {
		return array();
	}
	$query = new WP_Query(
		array(
			'post_type'      => 'product',
			'post_status'    => 'publish',
			'posts_per_page' => $limit,
			'post__not_in'   => array( $product->get_id() ),
			'tax_query'      => array(
				'relation' => 'AND',
				array(
					'taxonomy' => CTTEL_DEVICE_MODEL_TAX,
					'field'    => 'term_id',
					'terms'    => $terms,
				),
				array(
					'taxonomy' => 'product_cat',
					'field'    => 'slug',
					'terms'    => array( 'mobile-new', 'mobile-used' ),
				),
			),
		)
	);
	$out = array();
	foreach ( $query->posts as $post ) {
		$p = wc_get_product( $post );
		if ( $p instanceof WC_Product ) {
			$out[] = $p;
		}
	}
	return $out;
}

/** Archive filters — condition, subcategory, brand, storage. */
add_action(
	'pre_get_posts',
	static function ( WP_Query $query ): void {
		if ( is_admin() || ! $query->is_main_query() || ! function_exists( 'is_product_taxonomy' ) ) {
			return;
		}
		if ( ! ( is_shop() || is_product_taxonomy() ) ) {
			return;
		}
		if ( ! isset( $_GET['cttel_filter'] ) || '1' !== (string) wp_unslash( $_GET['cttel_filter'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			return;
		}

		$meta_query = (array) $query->get( 'meta_query' );
		$tax_query  = (array) $query->get( 'tax_query' );

		if ( ! empty( $_GET['cttel_condition'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			$cond = sanitize_key( wp_unslash( (string) $_GET['cttel_condition'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			if ( in_array( $cond, array( 'new', 'used' ), true ) ) {
				$meta_query[] = array(
					'key'     => CTTEL_META_CONDITION,
					'value'   => $cond,
					'compare' => '=',
				);
			}
		}

		if ( ! empty( $_GET['cttel_subcat'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			$slug = sanitize_title( wp_unslash( (string) $_GET['cttel_subcat'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			if ( '' !== $slug ) {
				$tax_query[] = array(
					'taxonomy' => 'product_cat',
					'field'    => 'slug',
					'terms'    => array( $slug ),
				);
			}
		}

		if ( ! empty( $meta_query ) ) {
			$query->set( 'meta_query', $meta_query );
		}
		if ( ! empty( $tax_query ) ) {
			$query->set( 'tax_query', $tax_query );
		}
	},
	25
);

/**
 * Extra filter fields in archive drawer.
 */
function cttel_catalog_render_archive_filters(): void {
	$condition = isset( $_GET['cttel_condition'] ) ? sanitize_key( wp_unslash( (string) $_GET['cttel_condition'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	$subcat    = isset( $_GET['cttel_subcat'] ) ? sanitize_title( wp_unslash( (string) $_GET['cttel_subcat'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	if ( cttel_catalog_has_used_inventory() ) {
		?>
		<fieldset class="cttel-ms-filter-group">
			<legend><?php esc_html_e( 'نو / کارکرده', 'cttel-store' ); ?></legend>
			<select name="cttel_condition" class="cttel-ms-filter-select">
				<option value=""><?php esc_html_e( 'همه', 'cttel-store' ); ?></option>
				<option value="new" <?php selected( $condition, 'new' ); ?>><?php esc_html_e( 'نو', 'cttel-store' ); ?></option>
				<option value="used" <?php selected( $condition, 'used' ); ?>><?php esc_html_e( 'کارکرده', 'cttel-store' ); ?></option>
			</select>
		</fieldset>
		<?php
	}
	$parent = null;
	if ( is_product_category() ) {
		$obj = get_queried_object();
		if ( $obj instanceof WP_Term ) {
			$parent = $obj->parent ? get_term( (int) $obj->parent, 'product_cat' ) : $obj;
		}
	}
	if ( $parent instanceof WP_Term ) {
		$children = get_terms(
			array(
				'taxonomy'   => 'product_cat',
				'parent'     => (int) $parent->term_id,
				'hide_empty' => true,
			)
		);
		if ( ! is_wp_error( $children ) && ! empty( $children ) ) {
			?>
			<fieldset class="cttel-ms-filter-group">
				<legend><?php esc_html_e( 'زیردسته', 'cttel-store' ); ?></legend>
				<select name="cttel_subcat" class="cttel-ms-filter-select">
					<option value=""><?php esc_html_e( 'همه', 'cttel-store' ); ?></option>
					<?php foreach ( $children as $child ) : ?>
						<?php if ( ! $child instanceof WP_Term ) {
							continue;
						} ?>
						<option value="<?php echo esc_attr( $child->slug ); ?>" <?php selected( $subcat, $child->slug ); ?>><?php echo esc_html( $child->name ); ?></option>
					<?php endforeach; ?>
				</select>
			</fieldset>
			<?php
		}
	}
}

/**
 * Admin-configurable consultation / lead URL for installment (not hard-coded /contact/).
 */
function cttel_installment_consultation_url(): string {
	$url = get_option( CTTEL_OPTION_INSTALLMENT_LEAD_URL, '' );
	if ( is_string( $url ) && '' !== trim( $url ) ) {
		return esc_url( trim( $url ) );
	}
	return '';
}

/**
 * Used-phone supply request page (existing site page).
 */
function cttel_used_phone_request_url(): string {
	$page = get_page_by_path( 'used-phone-request' );
	if ( $page instanceof WP_Post ) {
		return (string) get_permalink( $page );
	}
	return home_url( '/used-phone-request/' );
}

function cttel_installment_consultation_label(): string {
	$label = get_option( CTTEL_OPTION_INSTALLMENT_LEAD_LBL, '' );
	if ( is_string( $label ) && '' !== trim( $label ) ) {
		return trim( $label );
	}
	return __( 'مشاوره خرید اقساطی', 'cttel-store' );
}

/** Installment informational page. */
function cttel_installment_default_page_html(): string {
	$shop     = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
	$lead_url = cttel_installment_consultation_url();
	$lead_lbl = cttel_installment_consultation_label();
	ob_start();
	?>
	<div class="cttel-installment-page">
		<h1 class="cttel-installment-page__title"><?php esc_html_e( 'خرید اقساطی CTTEL', 'cttel-store' ); ?></h1>
		<p class="cttel-installment-page__intro"><?php esc_html_e( 'خرید اقساطی CTTEL به‌صورت حضوری و پس از بررسی شرایط انجام می‌شود.', 'cttel-store' ); ?></p>

		<h2><?php esc_html_e( 'فرایند درخواست و مشاوره', 'cttel-store' ); ?></h2>
		<ol class="cttel-installment-page__steps">
			<li><?php esc_html_e( 'با تیم فروش تماس بگیرید یا درخواست مشاوره ثبت کنید.', 'cttel-store' ); ?></li>
			<li><?php esc_html_e( 'شرایط فعلی طرح‌ها و مدارک موردنیاز را از پشتیبانی دریافت کنید.', 'cttel-store' ); ?></li>
			<li><?php esc_html_e( 'پس از تأیید اولیه، مراحل بعدی (حضوری یا هماهنگ‌شده) را طی کنید.', 'cttel-store' ); ?></li>
		</ol>

		<h2><?php esc_html_e( 'نکات مهم', 'cttel-store' ); ?></h2>
		<ul class="cttel-installment-page__list">
			<li><?php esc_html_e( 'طرح‌ها، سقف اعتبار و الزامات ممکن است متفاوت باشد و فقط پس از بررسی CTTEL اعلام می‌شود.', 'cttel-store' ); ?></li>
			<li><?php esc_html_e( 'تأیید نهایی و زمان‌بندی اقساط در فروشگاه تعیین می‌شود — نه به‌صورت خودکار آنلاین.', 'cttel-store' ); ?></li>
			<li><?php esc_html_e( 'برای خرید نقدی و پرداخت آنلاین، از فهرست محصولات و سبد خرید استفاده کنید.', 'cttel-store' ); ?></li>
		</ul>

		<p class="cttel-installment-page__note"><?php esc_html_e( 'CTTEL هیچ نرخ، بانک، یا وعده تأیید فوری آنلاین در این صفحه اعلام نمی‌کند. برای شرایط به‌روز با ما در ارتباط باشید.', 'cttel-store' ); ?></p>

		<div class="cttel-installment-page__actions">
			<a class="cttel-ms-btn cttel-ms-btn--primary" href="<?php echo esc_url( $shop ); ?>"><?php esc_html_e( 'مشاهده محصولات (خرید نقدی)', 'cttel-store' ); ?></a>
			<?php if ( '' !== $lead_url ) : ?>
				<a class="cttel-ms-btn cttel-ms-btn--outline" href="<?php echo esc_url( $lead_url ); ?>"><?php echo esc_html( $lead_lbl ); ?></a>
			<?php else : ?>
				<p class="cttel-installment-page__admin-hint"><?php esc_html_e( 'مدیر سایت: لینک «مشاوره خرید اقساطی» را در تنظیمات → عمومی تنظیم کنید.', 'cttel-store' ); ?></p>
			<?php endif; ?>
		</div>
	</div>
	<?php
	return (string) ob_get_clean();
}

add_filter(
	'the_content',
	static function ( string $content ): string {
		if ( ! is_page( 'installment' ) || ! in_the_loop() || ! is_main_query() ) {
			return $content;
		}
		$custom = get_option( CTTEL_OPTION_INSTALLMENT, '' );
		if ( is_string( $custom ) && '' !== trim( $custom ) ) {
			return wp_kses_post( $custom );
		}
		return cttel_installment_default_page_html();
	},
	12
);

add_action(
	'admin_init',
	static function (): void {
		register_setting(
			'general',
			CTTEL_OPTION_INSTALLMENT,
			array(
				'type'              => 'string',
				'sanitize_callback' => 'wp_kses_post',
				'default'           => '',
			)
		);
		register_setting(
			'general',
			CTTEL_OPTION_INSTALLMENT_LEAD_URL,
			array(
				'type'              => 'string',
				'sanitize_callback' => 'esc_url_raw',
				'default'           => '',
			)
		);
		register_setting(
			'general',
			CTTEL_OPTION_INSTALLMENT_LEAD_LBL,
			array(
				'type'              => 'string',
				'sanitize_callback' => 'sanitize_text_field',
				'default'           => '',
			)
		);
		add_settings_field(
			CTTEL_OPTION_INSTALLMENT,
			__( 'متن صفحه خرید اقساطی (HTML)', 'cttel-store' ),
			static function (): void {
				$value = get_option( CTTEL_OPTION_INSTALLMENT, '' );
				printf(
					'<textarea name="%1$s" rows="8" class="large-text code">%2$s</textarea><p class="description">%3$s</p>',
					esc_attr( CTTEL_OPTION_INSTALLMENT ),
					esc_textarea( is_string( $value ) ? $value : '' ),
					esc_html__( 'خالی = متن پیش‌فرض اطلاع‌رسانی (بدون نرخ/مدرک ساختگی).', 'cttel-store' )
				);
			},
			'general'
		);
		add_settings_field(
			CTTEL_OPTION_INSTALLMENT_LEAD_URL,
			__( 'لینک CTA مشاوره اقساطی', 'cttel-store' ),
			static function (): void {
				$value = get_option( CTTEL_OPTION_INSTALLMENT_LEAD_URL, '' );
				printf(
					'<input type="url" name="%1$s" value="%2$s" class="regular-text" placeholder="https://..." /><p class="description">%3$s</p>',
					esc_attr( CTTEL_OPTION_INSTALLMENT_LEAD_URL ),
					esc_attr( is_string( $value ) ? $value : '' ),
					esc_html__( 'صفحه تماس، واتساپ، فرم یا هر URL معتبر — در صفحه اقساط و بخش اقساطی خانه نمایش داده می‌شود.', 'cttel-store' )
				);
			},
			'general'
		);
		add_settings_field(
			CTTEL_OPTION_INSTALLMENT_LEAD_LBL,
			__( 'عنوان دکمه مشاوره اقساطی', 'cttel-store' ),
			static function (): void {
				$value = get_option( CTTEL_OPTION_INSTALLMENT_LEAD_LBL, '' );
				printf(
					'<input type="text" name="%1$s" value="%2$s" class="regular-text" placeholder="%3$s" />',
					esc_attr( CTTEL_OPTION_INSTALLMENT_LEAD_LBL ),
					esc_attr( is_string( $value ) ? $value : '' ),
					esc_attr__( 'مشاوره خرید اقساطی', 'cttel-store' )
				);
			},
			'general'
		);
	}
);

/**
 * Whether any published used-phone products exist (for filter UI).
 */
function cttel_catalog_has_used_inventory(): bool {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return false;
	}
	$found = wc_get_products(
		array(
			'limit'      => 1,
			'status'     => 'publish',
			'meta_key'   => CTTEL_META_CONDITION,
			'meta_value' => 'used',
			'return'     => 'ids',
		)
	);
	return ! empty( $found );
}

/**
 * Homepage section readiness report (no redesign).
 *
 * @return array<string, mixed>
 */
function cttel_homepage_data_sections_report(): array {
	$sections = array(
		'پیشنهادهای ویژه'     => array(
			'source'  => 'wc_get_products(on_sale + featured fallback)',
			'ready'   => function_exists( 'wc_get_products' ),
			'helper'  => 'cttel_ms_home_products()',
		),
		'گوشی‌های نو'          => array(
			'source'  => 'product_cat: mobile-new',
			'ready'   => (bool) get_term_by( 'slug', 'mobile-new', 'product_cat' ),
			'helper'  => 'cttel_catalog_products_in_category(mobile-new)',
		),
		'گوشی‌های کارکرده'     => array(
			'source'  => 'product_cat: mobile-used + used meta',
			'ready'   => (bool) get_term_by( 'slug', 'mobile-used', 'product_cat' ),
			'helper'  => 'cttel_catalog_products_in_category(mobile-used)',
		),
		'لوازم جانبی پرفروش'   => array(
			'source'  => 'product_cat: accessories (orderby popularity)',
			'ready'   => (bool) get_term_by( 'slug', 'accessories', 'product_cat' ),
			'helper'  => 'wc_get_products category accessories orderby popularity',
		),
		'گجت‌ها'               => array(
			'source'  => 'product_cat: gadget',
			'ready'   => (bool) get_term_by( 'slug', 'gadget', 'product_cat' ),
			'helper'  => 'cttel_catalog_products_in_category(gadget)',
		),
		'خرید اقساطی حضوری'    => array(
			'source'  => 'cttel_ms_home_render_installment() → /installment/',
			'ready'   => true,
			'helper'  => 'informational CTA only',
		),
		'اعتماد به CTTEL'      => array(
			'source'  => 'cttel_ms_home_render_trust() static list',
			'ready'   => true,
			'helper'  => 'editable later via theme mod / options',
		),
	);
	return $sections;
}

/**
 * @return WC_Product[]
 */
function cttel_catalog_products_in_category( string $slug, int $limit = 8 ): array {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return array();
	}
	$term = get_term_by( 'slug', $slug, 'product_cat' );
	if ( ! $term instanceof WP_Term ) {
		return array();
	}
	return wc_get_products(
		array(
			'limit'    => $limit,
			'status'   => 'publish',
			'category' => array( $slug ),
			'orderby'  => 'date',
			'order'    => 'DESC',
		)
	);
}

/**
 * @return array<string, mixed>
 */
function cttel_catalog_audit_snapshot(): array {
	$cats = array();
	foreach ( cttel_catalog_category_tree() as $slug => $def ) {
		$parent = get_term_by( 'slug', $slug, 'product_cat' );
		$row    = array(
			'slug'     => $slug,
			'name'     => $def['name'],
			'exists'   => $parent instanceof WP_Term,
			'children' => array(),
		);
		if ( $parent instanceof WP_Term ) {
			foreach ( $def['children'] as $child_slug => $child_name ) {
				$child = get_term_by( 'slug', $child_slug, 'product_cat' );
				$row['children'][] = array(
					'slug'   => $child_slug,
					'name'   => $child_name,
					'exists' => $child instanceof WP_Term,
				);
			}
		}
		$cats[] = $row;
	}
	return array(
		'version'          => CTTEL_CATALOG_VERSION,
		'bootstrapped'     => (bool) get_option( CTTEL_CATALOG_BOOT_KEY ),
		'categories'       => $cats,
		'device_model_tax' => taxonomy_exists( CTTEL_DEVICE_MODEL_TAX ),
		'homepage_sections'=> cttel_homepage_data_sections_report(),
	);
}

add_action(
	'template_redirect',
	static function (): void {
		if ( ! cttel_is_staging_catalog_site() || ! isset( $_GET['cttel_staging_wc_audit'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			return;
		}
		if ( 'catalog' !== (string) wp_unslash( $_GET['cttel_staging_wc_audit'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			return;
		}
		wp_send_json( cttel_catalog_audit_snapshot(), 200 );
	},
	6
);
