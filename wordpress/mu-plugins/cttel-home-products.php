<?php
/**
 * CTTEL homepage product grids — images required, no fake inventory display.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Whether product has a real featured image (not empty). */
function cttel_product_has_thumbnail( WC_Product $product ): bool {
	$thumb_id = $product->get_image_id();
	return $thumb_id > 0;
}

/**
 * Featured / catalog products with thumbnails only.
 *
 * @return WC_Product[]
 */
function cttel_get_homepage_products( int $limit = 4, string $visibility = 'featured' ): array {
	$args = array(
		'limit'   => $limit * 3,
		'status'  => 'publish',
		'orderby' => 'date',
		'order'   => 'DESC',
	);

	if ( 'featured' === $visibility ) {
		$args['featured'] = true;
	}

	$products = wc_get_products( $args );
	$out      = cttel_filter_homepage_products_with_thumbs( $products, $limit );

	if ( empty( $out ) && 'featured' === $visibility ) {
		unset( $args['featured'] );
		$products = wc_get_products( $args );
		$out      = cttel_filter_homepage_products_with_thumbs( $products, $limit );
	}

	return $out;
}

/**
 * @param WC_Product[] $products
 * @return WC_Product[]
 */
function cttel_filter_homepage_products_with_thumbs( array $products, int $limit ): array {
	$out = array();
	foreach ( $products as $product ) {
		if ( ! $product instanceof WC_Product || ! cttel_product_has_thumbnail( $product ) ) {
			continue;
		}
		$out[] = $product;
		if ( count( $out ) >= $limit ) {
			break;
		}
	}
	return $out;
}

/** Compact premium product card for homepage (avoids theme duplicate markup). */
function cttel_render_home_product_card( WC_Product $product ): string {
	$permalink = $product->get_permalink();
	$thumb_id  = $product->get_image_id();
	$image     = wp_get_attachment_image(
		$thumb_id,
		'woocommerce_thumbnail',
		false,
		array(
			'class'   => 'cttel-hp-card__img',
			'loading' => 'lazy',
			'alt'     => $product->get_name(),
		)
	);
	$badges    = function_exists( 'cttel_product_card_badges' )
		? cttel_product_card_badges( $product )
		: '';
	$stock     = function_exists( 'cttel_product_stock_label' )
		? cttel_product_stock_label( $product )
		: '';
	$stock_cls = function_exists( 'cttel_product_stock_class' )
		? cttel_product_stock_class( $product )
		: 'is-in-stock';

	$cart_url = $product->add_to_cart_url();
	$cart_txt = $product->add_to_cart_text();

	ob_start();
	?>
	<li <?php wc_product_class( 'cttel-hp-card', $product ); ?>>
		<a class="cttel-hp-card__link" href="<?php echo esc_url( $permalink ); ?>">
			<div class="cttel-hp-card__media">
				<?php echo $badges; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				<?php echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
			</div>
			<h3 class="cttel-hp-card__title"><?php echo esc_html( $product->get_name() ); ?></h3>
		</a>
		<div class="cttel-hp-card__meta">
			<div class="cttel-hp-card__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
			<p class="cttel-hp-card__stock <?php echo esc_attr( $stock_cls ); ?>"><?php echo esc_html( $stock ); ?></p>
		</div>
		<div class="cttel-hp-card__actions">
			<a href="<?php echo esc_url( $cart_url ); ?>" class="button cttel-hp-card__btn add_to_cart_button product_type_<?php echo esc_attr( $product->get_type() ); ?>" data-product_id="<?php echo esc_attr( (string) $product->get_id() ); ?>" data-product_sku="<?php echo esc_attr( $product->get_sku() ); ?>" aria-label="<?php echo esc_attr( $product->add_to_cart_description() ); ?>"><?php echo esc_html( $cart_txt ); ?></a>
		</div>
	</li>
	<?php
	return (string) ob_get_clean();
}

/** Render homepage special offers grid. */
function cttel_shortcode_special_products( $atts ): string {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return '';
	}

	$atts = shortcode_atts(
		array(
			'limit'      => 4,
			'visibility' => 'featured',
		),
		$atts,
		'cttel_special_products'
	);

	$limit    = max( 1, min( 8, (int) $atts['limit'] ) );
	$products = cttel_get_homepage_products( $limit, (string) $atts['visibility'] );

	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-section cttel-v2-special-products">
		<div class="cttel-container">
			<div class="cttel-v2-section-head">
				<h2 class="cttel-v2-heading">پیشنهادهای ویژه CTTEL</h2>
				<a class="cttel-v2-link-all" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">مشاهده همه</a>
			</div>
			<?php if ( empty( $products ) ) : ?>
				<p class="cttel-v2-lead"><?php esc_html_e( 'به‌زودی محصولات منتخب با تصویر در این بخش نمایش داده می‌شوند.', 'cttel-store' ); ?></p>
			<?php else : ?>
				<ul class="products cttel-products cttel-products--home columns-<?php echo esc_attr( (string) $limit ); ?>">
					<?php
					foreach ( $products as $product ) {
						echo cttel_render_home_product_card( $product ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
					}
					?>
				</ul>
			<?php endif; ?>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_special_products', 'cttel_shortcode_special_products' );

add_filter(
	'woocommerce_product_add_to_cart_text',
	static function ( string $text ): string {
		if ( is_front_page() ) {
			return __( 'افزودن به سبد', 'cttel-store' );
		}
		return $text;
	}
);
