<?php
/**
 * Product loop card — mobile storefront archive.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

global $product;

if ( ! $product instanceof WC_Product ) {
	return;
}

$image = cttel_ms_product_card_image_html( $product, 'cttel-ms-pcard__img' );
?>
<li <?php wc_product_class( 'cttel-ms-pcard', $product ); ?>>
	<a class="cttel-ms-pcard__link" href="<?php echo esc_url( $product->get_permalink() ); ?>">
		<div class="cttel-ms-pcard__media">
			<?php
			if ( $product->is_on_sale() ) {
				echo '<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--sale">' . esc_html__( 'حراج', 'cttel-store' ) . '</span>';
			} elseif ( function_exists( 'cttel_product_has_installment' ) && cttel_product_has_installment( $product ) ) {
				echo '<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--installment">' . esc_html__( 'اقساطی', 'cttel-store' ) . '</span>';
			}
			echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			?>
		</div>
		<h2 class="cttel-ms-pcard__name woocommerce-loop-product__title"><?php echo esc_html( $product->get_name() ); ?></h2>
	</a>
	<div class="cttel-ms-pcard__meta">
		<div class="cttel-ms-pcard__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
		<?php if ( function_exists( 'cttel_product_stock_label' ) ) : ?>
			<p class="cttel-ms-pcard__stock <?php echo esc_attr( cttel_product_stock_class( $product ) ); ?>">
				<?php echo esc_html( cttel_product_stock_label( $product ) ); ?>
			</p>
		<?php endif; ?>
	</div>
</li>
