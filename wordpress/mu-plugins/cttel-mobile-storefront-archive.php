<?php
/**
 * Shop & category archives — mobile storefront listing.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

function cttel_ms_is_product_archive(): bool {
	return function_exists( 'is_shop' ) && ( is_shop() || is_product_taxonomy() || is_product_tag() );
}

function cttel_ms_archive_title(): string {
	if ( is_product_category() || is_product_tag() ) {
		$term = get_queried_object();
		if ( $term instanceof WP_Term ) {
			return $term->name;
		}
	}
	if ( is_shop() ) {
		return __( 'فروشگاه', 'cttel-store' );
	}
	return __( 'محصولات', 'cttel-store' );
}

function cttel_ms_archive_back_url(): string {
	if ( function_exists( 'cttel_mobile_storefront_categories_url' ) ) {
		return cttel_mobile_storefront_categories_url();
	}
	return home_url( '/dastebandi/' );
}

/**
 * @return array<string, string>
 */
function cttel_ms_catalog_orderby_options(): array {
	return apply_filters(
		'woocommerce_catalog_orderby',
		array(
			'date'       => __( 'جدیدترین', 'cttel-store' ),
			'popularity' => __( 'محبوب‌ترین', 'cttel-store' ),
			'price'      => __( 'ارزان‌ترین', 'cttel-store' ),
			'price-desc' => __( 'گران‌ترین', 'cttel-store' ),
		)
	);
}

/**
 * Filterable attribute taxonomies that have terms with products in current archive.
 *
 * @return array<int, array{taxonomy: string, label: string, terms: WP_Term[]}>
 */
function cttel_ms_archive_filter_groups(): array {
	if ( ! function_exists( 'wc_get_attribute_taxonomies' ) ) {
		return array();
	}
	$groups = array();
	foreach ( wc_get_attribute_taxonomies() as $attribute ) {
		$taxonomy = wc_attribute_taxonomy_name( $attribute->attribute_name );
		if ( ! taxonomy_exists( $taxonomy ) ) {
			continue;
		}
		$terms = get_terms(
			array(
				'taxonomy'   => $taxonomy,
				'hide_empty' => true,
			)
		);
		if ( is_wp_error( $terms ) || empty( $terms ) ) {
			continue;
		}
		$groups[] = array(
			'taxonomy' => $taxonomy,
			'label'    => wc_attribute_label( $taxonomy ),
			'terms'    => $terms,
		);
	}
	return $groups;
}

function cttel_ms_archive_filters_active(): bool {
	return isset( $_GET['cttel_filter'] ) && '1' === (string) wp_unslash( $_GET['cttel_filter'] ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_ms_is_product_archive() && cttel_mobile_storefront_uses_shell() ) {
			$classes[] = 'cttel-ms-archive';
		}
		return $classes;
	}
);

function cttel_ms_use_ms_product_card_template(): bool {
	if ( ! cttel_mobile_storefront_uses_shell() ) {
		return false;
	}
	if ( cttel_ms_is_product_archive() ) {
		return true;
	}
	if ( function_exists( 'cttel_ms_is_product_search' ) && cttel_ms_is_product_search() ) {
		return true;
	}
	return function_exists( 'cttel_ms_is_single_product' ) && cttel_ms_is_single_product();
}

function cttel_ms_product_card_template_path(): string {
	return __DIR__ . '/templates/content-product-ms.php';
}

add_filter(
	'woocommerce_locate_template',
	static function ( string $template, string $template_name, string $template_path ): string {
		if ( 'content-product.php' !== $template_name || ! cttel_ms_use_ms_product_card_template() ) {
			return $template;
		}
		$custom = cttel_ms_product_card_template_path();
		return is_readable( $custom ) ? $custom : $template;
	},
	999,
	3
);

add_filter(
	'wc_get_template_part',
	static function ( $template, $slug, $name ) {
		if ( 'content' !== $slug || 'product' !== $name || ! cttel_ms_use_ms_product_card_template() ) {
			return $template;
		}
		$custom = cttel_ms_product_card_template_path();
		return is_readable( $custom ) ? $custom : $template;
	},
	999,
	3
);

add_filter(
	'wc_get_template',
	static function ( $template, $template_name, $args, $template_path, $default_path ) {
		if ( 'content-product.php' !== $template_name || ! cttel_ms_use_ms_product_card_template() ) {
			return $template;
		}
		$custom = cttel_ms_product_card_template_path();
		return is_readable( $custom ) ? $custom : $template;
	},
	999,
	5
);

add_action(
	'wp',
	static function (): void {
		if ( ! cttel_ms_use_ms_product_card_template() ) {
			return;
		}
		remove_all_actions( 'woocommerce_before_shop_loop_item_title' );
		remove_all_actions( 'woocommerce_after_shop_loop_item_title' );
	},
	999
);

/** Apply archive filters to main product query. */
add_action(
	'pre_get_posts',
	static function ( WP_Query $query ): void {
		if ( is_admin() || ! $query->is_main_query() || ! cttel_ms_is_product_archive() ) {
			return;
		}
		if ( ! cttel_ms_archive_filters_active() ) {
			return;
		}

		$meta_query = (array) $query->get( 'meta_query' );
		$tax_query  = (array) $query->get( 'tax_query' );

		if ( isset( $_GET['cttel_in_stock'] ) && '1' === (string) wp_unslash( $_GET['cttel_in_stock'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			$meta_query[] = array(
				'key'     => '_stock_status',
				'value'   => 'instock',
				'compare' => '=',
			);
		}

		if ( isset( $_GET['cttel_on_sale'] ) && '1' === (string) wp_unslash( $_GET['cttel_on_sale'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			$query->set( 'post__in', array_merge( array( 0 ), wc_get_product_ids_on_sale() ) );
		}

		$min_price = isset( $_GET['cttel_min_price'] ) ? wc_clean( wp_unslash( $_GET['cttel_min_price'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		$max_price = isset( $_GET['cttel_max_price'] ) ? wc_clean( wp_unslash( $_GET['cttel_max_price'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		if ( '' !== $min_price || '' !== $max_price ) {
			$meta_query[] = array(
				'key'     => '_price',
				'value'   => array( (float) ( '' === $min_price ? 0 : $min_price ), (float) ( '' === $max_price ? PHP_INT_MAX : $max_price ) ),
				'type'    => 'NUMERIC',
				'compare' => 'BETWEEN',
			);
		}

		foreach ( cttel_ms_archive_filter_groups() as $group ) {
			$key = 'cttel_attr_' . sanitize_key( $group['taxonomy'] );
			if ( empty( $_GET[ $key ] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
				continue;
			}
			$slug = sanitize_title( wp_unslash( (string) $_GET[ $key ] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			if ( '' === $slug ) {
				continue;
			}
			$tax_query[] = array(
				'taxonomy' => $group['taxonomy'],
				'field'    => 'slug',
				'terms'    => array( $slug ),
			);
		}

		if ( ! empty( $meta_query ) ) {
			$query->set( 'meta_query', $meta_query );
		}
		if ( ! empty( $tax_query ) ) {
			$query->set( 'tax_query', $tax_query );
		}
	},
	20
);

add_action(
	'wp',
	static function (): void {
		if ( ! cttel_ms_is_product_archive() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		remove_action( 'woocommerce_before_shop_loop', 'woocommerce_result_count', 20 );
		remove_action( 'woocommerce_before_shop_loop', 'woocommerce_catalog_ordering', 30 );
		add_filter( 'woocommerce_show_page_title', '__return_false' );
	},
	20
);

add_action(
	'woocommerce_before_main_content',
	static function (): void {
		if ( ! cttel_ms_is_product_archive() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		echo '<main class="cttel-ms-main cttel-ms-main--archive" id="cttel-ms-archive-main">';
		cttel_ms_archive_render_toolbar();
	},
	5
);

add_action(
	'woocommerce_after_main_content',
	static function (): void {
		if ( ! cttel_ms_is_product_archive() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		echo '</main>';
		cttel_ms_archive_render_filter_drawer();
	},
	50
);

function cttel_ms_archive_render_toolbar(): void {
	global $wp_query;
	$total   = $wp_query instanceof WP_Query ? (int) $wp_query->found_posts : 0;
	$orderby = isset( $_GET['orderby'] ) ? wc_clean( wp_unslash( (string) $_GET['orderby'] ) ) : 'date'; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	$options = cttel_ms_catalog_orderby_options();
	$action  = esc_url( remove_query_arg( array( 'paged' ) ) );
	?>
	<div class="cttel-ms-archive-head">
		<div class="cttel-ms-archive-head__row">
			<a class="cttel-ms-archive-head__back" href="<?php echo esc_url( cttel_ms_archive_back_url() ); ?>">
				<?php echo cttel_mobile_storefront_icon( 'chev', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				<span><?php esc_html_e( 'بازگشت', 'cttel-store' ); ?></span>
			</a>
			<div class="cttel-ms-archive-head__title-wrap">
				<h1 class="cttel-ms-archive-head__title"><?php echo esc_html( cttel_ms_archive_title() ); ?></h1>
				<?php if ( $total > 0 ) : ?>
					<p class="cttel-ms-archive-head__count"><?php echo esc_html( sprintf( _n( '%d کالا', '%d کالا', $total, 'cttel-store' ), $total ) ); ?></p>
				<?php endif; ?>
			</div>
			<div class="cttel-ms-archive-head__actions">
				<a class="cttel-ms-archive-head__search" href="#cttel-ms-archive-search" aria-label="<?php esc_attr_e( 'جستجو', 'cttel-store' ); ?>">
					<?php echo cttel_mobile_storefront_icon( 'search', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				</a>
				<a class="cttel-ms-archive-head__cart" href="<?php echo esc_url( cttel_mobile_storefront_cart_url() ); ?>" aria-label="<?php esc_attr_e( 'سبد خرید', 'cttel-store' ); ?>">
					<?php echo cttel_mobile_storefront_icon( 'cart', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<?php
					$count = cttel_mobile_storefront_cart_count();
					if ( $count > 0 ) {
						echo '<span class="cttel-ms-archive-head__cart-count">' . esc_html( (string) $count ) . '</span>';
					}
					?>
				</a>
			</div>
		</div>
		<div class="cttel-ms-archive-head__search-panel" id="cttel-ms-archive-search" hidden>
			<?php cttel_mobile_storefront_product_search_form(); ?>
		</div>
		<div class="cttel-ms-archive-toolbar">
			<form class="cttel-ms-archive-sort" method="get" action="<?php echo esc_url( $action ); ?>">
				<label class="screen-reader-text" for="cttel-ms-orderby"><?php esc_html_e( 'مرتب‌سازی', 'cttel-store' ); ?></label>
				<select id="cttel-ms-orderby" name="orderby" class="cttel-ms-archive-sort__select" onchange="this.form.submit()">
					<?php foreach ( $options as $value => $label ) : ?>
						<option value="<?php echo esc_attr( $value ); ?>" <?php selected( $orderby, $value ); ?>><?php echo esc_html( $label ); ?></option>
					<?php endforeach; ?>
				</select>
				<?php cttel_ms_archive_preserve_filter_fields(); ?>
			</form>
			<?php if ( cttel_ms_archive_has_filters_ui() ) : ?>
				<button type="button" class="cttel-ms-archive-filter-btn" data-cttel-ms-open-filters="1" aria-expanded="false" aria-controls="cttel-ms-filter-drawer">
					<?php esc_html_e( 'فیلتر', 'cttel-store' ); ?>
				</button>
			<?php endif; ?>
		</div>
	</div>
	<?php
}

function cttel_ms_archive_has_filters_ui(): bool {
	if ( ! empty( cttel_ms_archive_filter_groups() ) ) {
		return true;
	}
	if ( function_exists( 'cttel_catalog_has_used_inventory' ) && cttel_catalog_has_used_inventory() ) {
		return true;
	}
	if ( is_product_category() ) {
		$obj = get_queried_object();
		if ( $obj instanceof WP_Term ) {
			$parent = $obj->parent ? get_term( (int) $obj->parent, 'product_cat' ) : $obj;
			if ( $parent instanceof WP_Term ) {
				$children = get_terms(
					array(
						'taxonomy'   => 'product_cat',
						'parent'     => (int) $parent->term_id,
						'hide_empty' => true,
					)
				);
				if ( ! is_wp_error( $children ) && ! empty( $children ) ) {
					return true;
				}
			}
		}
	}
	// Price / availability filters are always meaningful on product archives.
	return cttel_ms_is_product_archive();
}

function cttel_ms_archive_filter_reset_url(): string {
	$remove = array( 'cttel_filter', 'cttel_in_stock', 'cttel_on_sale', 'cttel_min_price', 'cttel_max_price', 'cttel_condition', 'cttel_subcat', 'paged' );
	foreach ( cttel_ms_archive_filter_groups() as $group ) {
		$remove[] = 'cttel_attr_' . sanitize_key( $group['taxonomy'] );
	}
	return remove_query_arg( $remove );
}

function cttel_ms_archive_preserve_filter_fields(): void {
	$keys = array( 'cttel_filter', 'cttel_in_stock', 'cttel_on_sale', 'cttel_min_price', 'cttel_max_price', 'cttel_condition', 'cttel_subcat' );
	foreach ( $keys as $key ) {
		if ( ! isset( $_GET[ $key ] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			continue;
		}
		printf(
			'<input type="hidden" name="%1$s" value="%2$s" />',
			esc_attr( $key ),
			esc_attr( wc_clean( wp_unslash( (string) $_GET[ $key ] ) ) ) // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		);
	}
	foreach ( cttel_ms_archive_filter_groups() as $group ) {
		$key = 'cttel_attr_' . sanitize_key( $group['taxonomy'] );
		if ( empty( $_GET[ $key ] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			continue;
		}
		printf(
			'<input type="hidden" name="%1$s" value="%2$s" />',
			esc_attr( $key ),
			esc_attr( sanitize_title( wp_unslash( (string) $_GET[ $key ] ) ) ) // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		);
	}
}

function cttel_ms_archive_render_filter_drawer(): void {
	$groups = cttel_ms_archive_filter_groups();
	$action = esc_url( remove_query_arg( array( 'paged' ) ) );
	?>
	<div class="cttel-ms-filter-drawer" id="cttel-ms-filter-drawer" hidden aria-hidden="true">
		<div class="cttel-ms-filter-drawer__backdrop" data-cttel-ms-close-filters="1"></div>
		<div class="cttel-ms-filter-drawer__panel" role="dialog" aria-modal="true" aria-labelledby="cttel-ms-filter-title">
			<div class="cttel-ms-filter-drawer__head">
				<h2 id="cttel-ms-filter-title" class="cttel-ms-filter-drawer__title"><?php esc_html_e( 'فیلتر محصولات', 'cttel-store' ); ?></h2>
				<button type="button" class="cttel-ms-filter-drawer__close" data-cttel-ms-close-filters="1" aria-label="<?php esc_attr_e( 'بستن', 'cttel-store' ); ?>">×</button>
			</div>
			<form class="cttel-ms-filter-drawer__form" method="get" action="<?php echo esc_url( $action ); ?>">
				<input type="hidden" name="cttel_filter" value="1" />
				<?php if ( isset( $_GET['orderby'] ) ) : // phpcs:ignore WordPress.Security.NonceVerification.Recommended ?>
					<input type="hidden" name="orderby" value="<?php echo esc_attr( wc_clean( wp_unslash( (string) $_GET['orderby'] ) ) ); ?>" />
				<?php endif; ?>

				<fieldset class="cttel-ms-filter-group">
					<legend><?php esc_html_e( 'قیمت (تومان)', 'cttel-store' ); ?></legend>
					<div class="cttel-ms-filter-range">
						<input type="number" name="cttel_min_price" inputmode="numeric" placeholder="<?php esc_attr_e( 'حداقل', 'cttel-store' ); ?>" value="<?php echo isset( $_GET['cttel_min_price'] ) ? esc_attr( wc_clean( wp_unslash( (string) $_GET['cttel_min_price'] ) ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended ?>" />
						<span aria-hidden="true">—</span>
						<input type="number" name="cttel_max_price" inputmode="numeric" placeholder="<?php esc_attr_e( 'حداکثر', 'cttel-store' ); ?>" value="<?php echo isset( $_GET['cttel_max_price'] ) ? esc_attr( wc_clean( wp_unslash( (string) $_GET['cttel_max_price'] ) ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended ?>" />
					</div>
				</fieldset>

				<fieldset class="cttel-ms-filter-group">
					<legend><?php esc_html_e( 'موجودی', 'cttel-store' ); ?></legend>
					<label class="cttel-ms-filter-check">
						<input type="checkbox" name="cttel_in_stock" value="1" <?php checked( isset( $_GET['cttel_in_stock'] ) && '1' === (string) wp_unslash( $_GET['cttel_in_stock'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended ?> />
						<?php esc_html_e( 'فقط کالاهای موجود', 'cttel-store' ); ?>
					</label>
					<label class="cttel-ms-filter-check">
						<input type="checkbox" name="cttel_on_sale" value="1" <?php checked( isset( $_GET['cttel_on_sale'] ) && '1' === (string) wp_unslash( $_GET['cttel_on_sale'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended ?> />
						<?php esc_html_e( 'فقط حراج', 'cttel-store' ); ?>
					</label>
				</fieldset>

				<?php
				if ( function_exists( 'cttel_catalog_render_archive_filters' ) ) {
					cttel_catalog_render_archive_filters();
				}
				?>

				<?php foreach ( $groups as $group ) : ?>
					<?php
					$field = 'cttel_attr_' . sanitize_key( $group['taxonomy'] );
					$current = isset( $_GET[ $field ] ) ? sanitize_title( wp_unslash( (string) $_GET[ $field ] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
					?>
					<fieldset class="cttel-ms-filter-group">
						<legend><?php echo esc_html( $group['label'] ); ?></legend>
						<select name="<?php echo esc_attr( $field ); ?>" class="cttel-ms-filter-select">
							<option value=""><?php esc_html_e( 'همه', 'cttel-store' ); ?></option>
							<?php foreach ( $group['terms'] as $term ) : ?>
								<?php if ( ! $term instanceof WP_Term ) {
									continue;
								} ?>
								<option value="<?php echo esc_attr( $term->slug ); ?>" <?php selected( $current, $term->slug ); ?>><?php echo esc_html( $term->name ); ?></option>
							<?php endforeach; ?>
						</select>
					</fieldset>
				<?php endforeach; ?>

				<div class="cttel-ms-filter-drawer__actions">
					<button type="submit" class="cttel-ms-btn cttel-ms-btn--primary cttel-ms-filter-drawer__apply"><?php esc_html_e( 'اعمال فیلتر', 'cttel-store' ); ?></button>
					<a class="cttel-ms-filter-drawer__reset" href="<?php echo esc_url( cttel_ms_archive_filter_reset_url() ); ?>"><?php esc_html_e( 'پاک کردن', 'cttel-store' ); ?></a>
				</div>
			</form>
		</div>
	</div>
	<?php
}

function cttel_ms_archive_inline_js(): string {
	return <<<'JS'
(function () {
	const drawer = document.getElementById('cttel-ms-filter-drawer');
	const openBtn = document.querySelector('[data-cttel-ms-open-filters]');
	if (!drawer || !openBtn) return;
	const closeEls = drawer.querySelectorAll('[data-cttel-ms-close-filters]');
	function open() {
		drawer.hidden = false;
		drawer.setAttribute('aria-hidden', 'false');
		openBtn.setAttribute('aria-expanded', 'true');
		document.body.classList.add('cttel-ms-filter-open');
	}
	function close() {
		drawer.hidden = true;
		drawer.setAttribute('aria-hidden', 'true');
		openBtn.setAttribute('aria-expanded', 'false');
		document.body.classList.remove('cttel-ms-filter-open');
	}
	openBtn.addEventListener('click', open);
	closeEls.forEach(function (el) { el.addEventListener('click', close); });
	const searchToggle = document.querySelector('.cttel-ms-archive-head__search');
	const searchPanel = document.getElementById('cttel-ms-archive-search');
	if (searchToggle && searchPanel) {
		searchToggle.addEventListener('click', function (e) {
			e.preventDefault();
			searchPanel.hidden = !searchPanel.hidden;
		});
	}
})();
JS;
}

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! cttel_ms_is_product_archive() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		wp_register_script( 'cttel-ms-archive', false, array(), CTTEL_MOBILE_STOREFRONT_VERSION, true );
		wp_enqueue_script( 'cttel-ms-archive' );
		wp_add_inline_script( 'cttel-ms-archive', cttel_ms_archive_inline_js() );
		wp_dequeue_style( 'cttel-storefront' );
	},
	125
);

add_filter(
	'woocommerce_product_loop_start',
	static function ( string $html ): string {
		if ( ! cttel_ms_is_product_archive() || ! cttel_mobile_storefront_uses_shell() ) {
			return $html;
		}
		return preg_replace(
			'/class="([^"]*products[^"]*)"/',
			'class="$1 cttel-ms-products__grid cttel-ms-products__grid--archive"',
			$html,
			1
		) ?? $html;
	}
);
