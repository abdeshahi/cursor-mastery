<?php
/**
 * Categories hub — RTL split parent nav + child grid.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

const CTTEL_MS_CATEGORIES_QUERY_VAR = 'cttel_cat_hub';

add_action(
	'init',
	static function (): void {
		add_rewrite_rule( '^dastebandi/?$', 'index.php?' . CTTEL_MS_CATEGORIES_QUERY_VAR . '=1', 'top' );
	},
	10
);

add_filter(
	'query_vars',
	static function ( array $vars ): array {
		$vars[] = CTTEL_MS_CATEGORIES_QUERY_VAR;
		return $vars;
	}
);

function cttel_mobile_storefront_categories_url(): string {
	return home_url( '/dastebandi/' );
}

function cttel_mobile_storefront_is_categories_hub(): bool {
	return (bool) get_query_var( CTTEL_MS_CATEGORIES_QUERY_VAR )
		|| ( is_page() && 'dastebandi' === get_post_field( 'post_name', get_queried_object_id() ) );
}

add_filter(
	'template_include',
	static function ( string $template ): string {
		if ( ! cttel_mobile_storefront_is_categories_hub() ) {
			return $template;
		}
		$custom = __DIR__ . '/templates/cttel-categories-hub.php';
		return is_readable( $custom ) ? $custom : $template;
	},
	102
);

/**
 * @return WP_Term[]
 */
function cttel_ms_parent_product_categories(): array {
	if ( function_exists( 'cttel_get_quick_category_terms' ) ) {
		return cttel_get_quick_category_terms();
	}
	$exclude = array_filter( array( (int) get_option( 'default_product_cat', 0 ) ) );
	$terms   = get_terms(
		array(
			'taxonomy'   => 'product_cat',
			'hide_empty' => false,
			'parent'     => 0,
			'exclude'    => $exclude,
		)
	);
	return is_wp_error( $terms ) ? array() : $terms;
}

/**
 * @return WP_Term[]
 */
function cttel_ms_child_product_categories( int $parent_id ): array {
	$terms = get_terms(
		array(
			'taxonomy'   => 'product_cat',
			'hide_empty' => false,
			'parent'     => $parent_id,
		)
	);
	if ( is_wp_error( $terms ) || empty( $terms ) ) {
		return array();
	}
	usort(
		$terms,
		static function ( WP_Term $a, WP_Term $b ): int {
			$order_a = (int) get_term_meta( $a->term_id, 'order', true );
			$order_b = (int) get_term_meta( $b->term_id, 'order', true );
			if ( $order_a === $order_b ) {
				return strcasecmp( $a->name, $b->name );
			}
			return $order_a <=> $order_b;
		}
	);
	return $terms;
}

function cttel_ms_category_card_image( WP_Term $term ): string {
	$thumb_id = (int) get_term_meta( $term->term_id, 'thumbnail_id', true );
	if ( $thumb_id > 0 ) {
		$img = wp_get_attachment_image(
			$thumb_id,
			'woocommerce_thumbnail',
			false,
			array(
				'class'   => 'cttel-ms-cat-card__img',
				'loading' => 'lazy',
				'alt'     => $term->name,
			)
		);
		if ( $img ) {
			return $img;
		}
	}
	return '<span class="cttel-ms-cat-card__img cttel-ms-cat-card__img--fallback" aria-hidden="true">' . cttel_mobile_storefront_category_icon( $term ) . '</span>';
}

/**
 * Published products in a category when no child terms exist (max 12).
 *
 * @return WP_Post[]
 */
function cttel_ms_category_hub_products( WP_Term $term, int $limit = 12 ): array {
	$query = new WP_Query(
		array(
			'post_type'      => 'product',
			'post_status'    => 'publish',
			'posts_per_page' => $limit,
			'no_found_rows'  => true,
			'tax_query'      => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_tax_query
				array(
					'taxonomy'         => 'product_cat',
					'field'            => 'term_id',
					'terms'            => (int) $term->term_id,
					'include_children' => true,
				),
			),
		)
	);
	return $query->posts;
}

function cttel_ms_category_hub_product_card_image( WC_Product $product ): string {
	$thumb_id = $product->get_image_id();
	if ( $thumb_id > 0 ) {
		$img = wp_get_attachment_image(
			$thumb_id,
			'woocommerce_thumbnail',
			false,
			array(
				'class'   => 'cttel-ms-cat-card__img',
				'loading' => 'lazy',
				'alt'     => $product->get_name(),
			)
		);
		if ( $img ) {
			return $img;
		}
	}
	return '<span class="cttel-ms-cat-card__img cttel-ms-cat-card__img--fallback" aria-hidden="true"></span>';
}

function cttel_ms_categories_hub_render(): void {
	$parents = cttel_ms_parent_product_categories();
	if ( empty( $parents ) ) {
		echo '<p class="cttel-ms-empty">' . esc_html__( 'دسته‌بندی محصول یافت نشد.', 'cttel-store' ) . '</p>';
		return;
	}

	$initial = $parents[0];
	if ( isset( $_GET['cat'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		$slug = sanitize_title( wp_unslash( (string) $_GET['cat'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		foreach ( $parents as $term ) {
			if ( $term->slug === $slug ) {
				$initial = $term;
				break;
			}
		}
	}
	?>
	<div class="cttel-ms-cat-hub" data-cttel-cat-hub>
		<aside class="cttel-ms-cat-hub__nav" aria-label="<?php esc_attr_e( 'دسته‌های اصلی', 'cttel-store' ); ?>">
			<ul class="cttel-ms-cat-hub__nav-list">
				<?php foreach ( $parents as $index => $term ) : ?>
					<?php
					if ( ! $term instanceof WP_Term ) {
						continue;
					}
					$active = $term->term_id === $initial->term_id;
					?>
					<li>
						<button
							type="button"
							class="cttel-ms-cat-hub__nav-item<?php echo $active ? ' is-active' : ''; ?>"
							data-cttel-parent-id="<?php echo esc_attr( (string) $term->term_id ); ?>"
							aria-pressed="<?php echo $active ? 'true' : 'false'; ?>"
						>
							<span class="cttel-ms-cat-hub__nav-icon"><?php echo cttel_mobile_storefront_category_icon( $term ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
							<span class="cttel-ms-cat-hub__nav-label"><?php echo esc_html( $term->name ); ?></span>
						</button>
					</li>
				<?php endforeach; ?>
			</ul>
		</aside>
		<div class="cttel-ms-cat-hub__panels">
			<?php foreach ( $parents as $term ) : ?>
				<?php
				if ( ! $term instanceof WP_Term ) {
					continue;
				}
				$children = cttel_ms_child_product_categories( (int) $term->term_id );
				$visible  = $term->term_id === $initial->term_id;
				$shop_all = get_term_link( $term );
				?>
				<section
					class="cttel-ms-cat-hub__panel<?php echo $visible ? ' is-visible' : ''; ?>"
					data-cttel-panel-id="<?php echo esc_attr( (string) $term->term_id ); ?>"
					<?php echo $visible ? '' : 'hidden'; ?>
				>
					<a class="cttel-ms-cat-hub__panel-head" href="<?php echo esc_url( $shop_all ); ?>">
						<span class="cttel-ms-cat-hub__panel-title"><?php echo esc_html( sprintf( 'همه محصولات دسته %s', $term->name ) ); ?></span>
						<span class="cttel-ms-cat-hub__panel-chev"><?php echo cttel_mobile_storefront_icon( 'chev' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
					</a>
					<?php
					$panel_products = array();
					if ( empty( $children ) && function_exists( 'wc_get_product' ) ) {
						$panel_products = cttel_ms_category_hub_products( $term );
					}
					?>
					<?php if ( ! empty( $children ) ) : ?>
						<ul class="cttel-ms-cat-hub__grid">
							<?php foreach ( $children as $child ) : ?>
								<?php if ( ! $child instanceof WP_Term ) {
									continue;
								} ?>
								<li>
									<a class="cttel-ms-cat-card" href="<?php echo esc_url( get_term_link( $child ) ); ?>">
										<span class="cttel-ms-cat-card__media"><?php echo cttel_ms_category_card_image( $child ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
										<span class="cttel-ms-cat-card__name"><?php echo esc_html( $child->name ); ?></span>
									</a>
								</li>
							<?php endforeach; ?>
						</ul>
					<?php elseif ( ! empty( $panel_products ) ) : ?>
						<ul class="cttel-ms-cat-hub__grid">
							<?php foreach ( $panel_products as $post ) : ?>
								<?php
								$product = wc_get_product( $post );
								if ( ! $product instanceof WC_Product ) {
									continue;
								}
								?>
								<li>
									<a class="cttel-ms-cat-card" href="<?php echo esc_url( $product->get_permalink() ); ?>">
										<span class="cttel-ms-cat-card__media"><?php echo cttel_ms_category_hub_product_card_image( $product ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
										<span class="cttel-ms-cat-card__name"><?php echo esc_html( $product->get_name() ); ?></span>
									</a>
								</li>
							<?php endforeach; ?>
						</ul>
					<?php else : ?>
						<p class="cttel-ms-cat-hub__empty"><?php esc_html_e( 'محصولی در این دسته یافت نشد.', 'cttel-store' ); ?></p>
					<?php endif; ?>
				</section>
			<?php endforeach; ?>
		</div>
	</div>
	<?php
}

function cttel_mobile_storefront_categories_js(): string {
	return <<<'JS'
(function () {
	var root = document.querySelector('[data-cttel-cat-hub]');
	if (!root) return;
	var navButtons = root.querySelectorAll('[data-cttel-parent-id]');
	var panels = root.querySelectorAll('[data-cttel-panel-id]');
	function showPanel(id) {
		panels.forEach(function (panel) {
			var match = panel.getAttribute('data-cttel-panel-id') === id;
			panel.classList.toggle('is-visible', match);
			if (match) {
				panel.removeAttribute('hidden');
			} else {
				panel.setAttribute('hidden', 'hidden');
			}
		});
		navButtons.forEach(function (btn) {
			var active = btn.getAttribute('data-cttel-parent-id') === id;
			btn.classList.toggle('is-active', active);
			btn.setAttribute('aria-pressed', active ? 'true' : 'false');
		});
	}
	navButtons.forEach(function (btn) {
		btn.addEventListener('click', function () {
			showPanel(btn.getAttribute('data-cttel-parent-id'));
		});
	});
})();
JS;
}
