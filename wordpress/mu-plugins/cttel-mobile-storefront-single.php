<?php
/**
 * Single product page — mobile storefront.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

function cttel_ms_is_single_product(): bool {
	return function_exists( 'is_product' ) && is_product();
}

function cttel_ms_installment_url(): string {
	if ( function_exists( 'cttel_installment_default_url' ) ) {
		return cttel_installment_default_url();
	}
	$page = get_page_by_path( 'installment' );
	if ( $page instanceof WP_Post ) {
		return get_permalink( $page );
	}
	return home_url( '/installment/' );
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_ms_is_single_product() && cttel_mobile_storefront_uses_shell() ) {
			$classes[] = 'cttel-ms-single';
		}
		return $classes;
	}
);

add_action(
	'woocommerce_before_main_content',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		$back = wp_get_referer();
		if ( ! $back || false !== strpos( $back, 'add-to-cart' ) ) {
			$terms = get_the_terms( $product->get_id(), 'product_cat' );
			if ( is_array( $terms ) && ! empty( $terms ) && $terms[0] instanceof WP_Term ) {
				$back = get_term_link( $terms[0] );
			} else {
				$back = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
			}
		}
		?>
		<main class="cttel-ms-main cttel-ms-main--single" id="cttel-ms-single-main">
			<div class="cttel-ms-single-head">
				<a class="cttel-ms-single-head__back" href="<?php echo esc_url( is_string( $back ) ? $back : home_url( '/' ) ); ?>">
					<?php echo cttel_mobile_storefront_icon( 'chev', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<span><?php esc_html_e( 'بازگشت', 'cttel-store' ); ?></span>
				</a>
				<a class="cttel-ms-single-head__cart" href="<?php echo esc_url( cttel_mobile_storefront_cart_url() ); ?>" aria-label="<?php esc_attr_e( 'سبد خرید', 'cttel-store' ); ?>">
					<?php echo cttel_mobile_storefront_icon( 'cart', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				</a>
			</div>
		<?php
	},
	5
);

add_action(
	'woocommerce_after_main_content',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		echo '</main>';
	},
	50
);

add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		if ( function_exists( 'cttel_product_is_used' ) && cttel_product_is_used( $product ) ) {
			echo '<p class="cttel-ms-single__badge cttel-ms-single__badge--used">' . esc_html__( 'کارکرده', 'cttel-store' ) . '</p>';
		} elseif ( function_exists( 'cttel_product_is_new' ) && cttel_product_is_new( $product ) ) {
			echo '<p class="cttel-ms-single__badge cttel-ms-single__badge--new">' . esc_html__( 'نو', 'cttel-store' ) . '</p>';
		}
		if ( function_exists( 'cttel_product_stock_label' ) ) {
			printf(
				'<p class="cttel-ms-single__stock %1$s">%2$s</p>',
				esc_attr( cttel_product_stock_class( $product ) ),
				esc_html( cttel_product_stock_label( $product ) )
			);
		}
	},
	6
);

add_action(
	'woocommerce_after_add_to_cart_button',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		$url = cttel_ms_installment_url();
		printf(
			'<p class="cttel-ms-single__installment-note"><a class="cttel-ms-single__installment-link" href="%1$s">%2$s</a></p>',
			esc_url( $url ),
			esc_html__( 'اطلاعات خرید اقساطی (مشاوره / حضوری)', 'cttel-store' )
		);
	},
	15
);

add_action(
	'wp',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_meta', 40 );
	},
	20
);

add_filter(
	'woocommerce_output_related_products_args',
	static function ( array $args ): array {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return $args;
		}
		$args['posts_per_page'] = 4;
		$args['columns']        = 2;
		return $args;
	}
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		wp_dequeue_style( 'cttel-storefront' );
	},
	125
);
