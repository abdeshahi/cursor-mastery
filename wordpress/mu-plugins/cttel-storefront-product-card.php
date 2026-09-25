<?php
/**
 * Shared conversion-focused product cards (home, archive, search).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * Short spec line for cards (no invented values).
 */
function cttel_ms_product_card_spec_line( WC_Product $product ): string {
	if ( function_exists( 'cttel_product_is_used' ) && cttel_product_is_used( $product ) ) {
		$specs = function_exists( 'cttel_product_used_specs' ) ? cttel_product_used_specs( $product ) : array();
		$pick  = array();
		foreach ( array( 'حافظه', 'سلامت باتری', 'وضعیت ظاهری', 'رنگ' ) as $label ) {
			if ( ! empty( $specs[ $label ] ) ) {
				$pick[] = $label . ': ' . $specs[ $label ];
			}
			if ( count( $pick ) >= 2 ) {
				break;
			}
		}
		return implode( ' · ', $pick );
	}
	$parts = array();
	if ( function_exists( 'wc_get_product_terms' ) ) {
		$brand_tax = wc_attribute_taxonomy_name( 'brand' );
		if ( taxonomy_exists( $brand_tax ) ) {
			$terms = wc_get_product_terms( $product->get_id(), $brand_tax, array( 'number' => 1 ) );
			if ( ! empty( $terms[0]->name ) ) {
				$parts[] = $terms[0]->name;
			}
		}
		$storage_tax = wc_attribute_taxonomy_name( 'storage' );
		if ( taxonomy_exists( $storage_tax ) ) {
			$terms = wc_get_product_terms( $product->get_id(), $storage_tax, array( 'number' => 1 ) );
			if ( ! empty( $terms[0]->name ) ) {
				$parts[] = $terms[0]->name;
			}
		}
	}
	return implode( ' · ', $parts );
}

/**
 * @param array{variant?: string, show_cta?: bool} $args
 */
function cttel_ms_render_product_card( WC_Product $product, array $args = array() ): string {
	$variant  = $args['variant'] ?? 'grid';
	$show_cta = $args['show_cta'] ?? true;
	$image    = cttel_ms_product_card_image_html( $product, 'cttel-ms-pcard__img' );
	$spec     = cttel_ms_product_card_spec_line( $product );
	$stock    = function_exists( 'cttel_product_stock_label' ) ? cttel_product_stock_label( $product ) : '';
	$stock_cl = function_exists( 'cttel_product_stock_class' ) ? cttel_product_stock_class( $product ) : '';

	ob_start();
	?>
	<li <?php wc_product_class( 'cttel-ms-pcard cttel-ms-pcard--' . esc_attr( $variant ), $product ); ?>>
		<a class="cttel-ms-pcard__link" href="<?php echo esc_url( $product->get_permalink() ); ?>">
			<div class="cttel-ms-pcard__media">
				<?php
				if ( function_exists( 'cttel_product_is_used' ) && cttel_product_is_used( $product ) ) {
					echo '<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--used">' . esc_html__( 'کارکرده', 'cttel-store' ) . '</span>';
				} elseif ( function_exists( 'cttel_product_is_new' ) && cttel_product_is_new( $product ) ) {
					echo '<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--new">' . esc_html__( 'نو', 'cttel-store' ) . '</span>';
				} elseif ( $product->is_on_sale() ) {
					echo '<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--sale">' . esc_html__( 'حراج', 'cttel-store' ) . '</span>';
				}
				echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
				?>
			</div>
			<h3 class="cttel-ms-pcard__name woocommerce-loop-product__title"><?php echo esc_html( $product->get_name() ); ?></h3>
		</a>
		<div class="cttel-ms-pcard__meta">
			<?php if ( '' !== $spec ) : ?>
				<p class="cttel-ms-pcard__spec"><?php echo esc_html( $spec ); ?></p>
			<?php endif; ?>
			<div class="cttel-ms-pcard__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
			<?php if ( '' !== $stock ) : ?>
				<p class="cttel-ms-pcard__stock <?php echo esc_attr( $stock_cl ); ?>"><?php echo esc_html( $stock ); ?></p>
			<?php endif; ?>
			<?php if ( $show_cta ) : ?>
				<a class="cttel-ms-pcard__cta cttel-ms-btn cttel-ms-btn--primary" href="<?php echo esc_url( $product->get_permalink() ); ?>">
					<?php esc_html_e( 'مشاهده محصول', 'cttel-store' ); ?>
				</a>
			<?php endif; ?>
		</div>
	</li>
	<?php
	return (string) ob_get_clean();
}
