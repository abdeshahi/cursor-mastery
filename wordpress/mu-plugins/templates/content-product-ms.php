<?php
/**
 * Product loop card — mobile storefront archive / search.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

global $product;

if ( ! $product instanceof WC_Product ) {
	return;
}

if ( function_exists( 'cttel_ms_render_product_card' ) ) {
	// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	echo cttel_ms_render_product_card( $product, array( 'variant' => 'grid', 'show_cta' => true ) );
	return;
}

$image = cttel_ms_product_card_image_html( $product, 'cttel-ms-pcard__img' );
?>
<li <?php wc_product_class( 'cttel-ms-pcard', $product ); ?>>
	<a class="cttel-ms-pcard__link" href="<?php echo esc_url( $product->get_permalink() ); ?>">
		<div class="cttel-ms-pcard__media"><?php echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
		<h2 class="cttel-ms-pcard__name woocommerce-loop-product__title"><?php echo esc_html( $product->get_name() ); ?></h2>
	</a>
	<div class="cttel-ms-pcard__meta">
		<div class="cttel-ms-pcard__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
	</div>
</li>
