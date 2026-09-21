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
				<ul class="products cttel-products cttel-products--featured columns-<?php echo esc_attr( (string) $limit ); ?>">
					<?php
					global $post;
					foreach ( $products as $product ) {
						$post_object = get_post( $product->get_id() );
						if ( ! $post_object ) {
							continue;
						}
						$post               = $post_object; // phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited
						$GLOBALS['product'] = $product; // phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited
						setup_postdata( $post_object );
						wc_get_template_part( 'content', 'product' );
					}
					wp_reset_postdata();
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
