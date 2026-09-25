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
		return '';
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
 * Compact used-phone facts for card chips.
 *
 * @return array<int, string>
 */
function cttel_ms_product_card_used_chips( WC_Product $product ): array {
	if ( ! function_exists( 'cttel_product_is_used' ) || ! cttel_product_is_used( $product ) ) {
		return array();
	}
	$specs = function_exists( 'cttel_product_used_specs' ) ? cttel_product_used_specs( $product ) : array();
	if ( empty( $specs ) ) {
		return array();
	}
	$order = array(
		__( 'مدل', 'cttel-store' ),
		__( 'حافظه', 'cttel-store' ),
		__( 'سلامت باتری', 'cttel-store' ),
		__( 'وضعیت ظاهری', 'cttel-store' ),
	);
	$chips = array();
	foreach ( $order as $label ) {
		if ( empty( $specs[ $label ] ) ) {
			continue;
		}
		$chips[] = $label . ': ' . $specs[ $label ];
		if ( count( $chips ) >= 3 ) {
			break;
		}
	}
	return $chips;
}

/**
 * @param array{variant?: string, show_cta?: bool} $args
 */
function cttel_ms_render_product_card( WC_Product $product, array $args = array() ): string {
	$variant  = $args['variant'] ?? 'grid';
	$show_cta = $args['show_cta'] ?? true;
	$image    = cttel_ms_product_card_image_html( $product, 'cttel-ms-pcard__img' );
	$spec     = cttel_ms_product_card_spec_line( $product );
	$used_chips = cttel_ms_product_card_used_chips( $product );
	$stock    = function_exists( 'cttel_product_stock_label' ) ? cttel_product_stock_label( $product ) : '';
	$stock_cl = function_exists( 'cttel_product_stock_class' ) ? cttel_product_stock_class( $product ) : '';
	$is_used  = function_exists( 'cttel_product_is_used' ) && cttel_product_is_used( $product );
	$is_new   = function_exists( 'cttel_product_is_new' ) && cttel_product_is_new( $product );
	$in_stock = $product->is_in_stock();
	$show_installment = function_exists( 'cttel_product_has_installment' )
		&& cttel_product_has_installment( $product )
		&& ! $is_new;

	$cta_label = __( 'مشاهده محصول', 'cttel-store' );
	if ( $in_stock && ( $is_used || $is_new ) ) {
		$cta_label = __( 'جزئیات و خرید', 'cttel-store' );
	}

	ob_start();
	?>
	<li <?php wc_product_class( 'cttel-ms-pcard cttel-ms-pcard--' . esc_attr( $variant ), $product ); ?>>
		<a class="cttel-ms-pcard__link" href="<?php echo esc_url( $product->get_permalink() ); ?>">
			<div class="cttel-ms-pcard__media">
				<div class="cttel-ms-pcard__badges">
					<?php if ( $is_used ) : ?>
						<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--used"><?php esc_html_e( 'کارکرده', 'cttel-store' ); ?></span>
					<?php elseif ( $is_new ) : ?>
						<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--new"><?php esc_html_e( 'نو', 'cttel-store' ); ?></span>
					<?php elseif ( $product->is_on_sale() ) : ?>
						<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--sale"><?php esc_html_e( 'حراج', 'cttel-store' ); ?></span>
					<?php endif; ?>
					<?php if ( $in_stock && '' !== $stock ) : ?>
						<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--stock"><?php echo esc_html( $stock ); ?></span>
					<?php endif; ?>
					<?php if ( $show_installment ) : ?>
						<span class="cttel-ms-pcard__badge cttel-ms-pcard__badge--installment"><?php esc_html_e( 'اقساطی', 'cttel-store' ); ?></span>
					<?php endif; ?>
				</div>
				<?php echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
			</div>
			<h3 class="cttel-ms-pcard__name woocommerce-loop-product__title"><?php echo esc_html( $product->get_name() ); ?></h3>
		</a>
		<div class="cttel-ms-pcard__meta">
			<?php if ( ! empty( $used_chips ) ) : ?>
				<ul class="cttel-ms-pcard__chips" aria-label="<?php esc_attr_e( 'خلاصه مشخصات', 'cttel-store' ); ?>">
					<?php foreach ( $used_chips as $chip ) : ?>
						<li><?php echo esc_html( $chip ); ?></li>
					<?php endforeach; ?>
				</ul>
			<?php elseif ( '' !== $spec ) : ?>
				<p class="cttel-ms-pcard__spec"><?php echo esc_html( $spec ); ?></p>
			<?php endif; ?>
			<div class="cttel-ms-pcard__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
			<?php if ( '' !== $stock ) : ?>
				<p class="cttel-ms-pcard__stock <?php echo esc_attr( $stock_cl ); ?>"><?php echo esc_html( $stock ); ?></p>
			<?php endif; ?>
			<?php if ( $show_cta ) : ?>
				<a class="cttel-ms-pcard__cta cttel-ms-btn cttel-ms-btn--primary" href="<?php echo esc_url( $product->get_permalink() ); ?>">
					<?php echo esc_html( $cta_label ); ?>
				</a>
			<?php endif; ?>
		</div>
	</li>
	<?php
	return (string) ob_get_clean();
}
