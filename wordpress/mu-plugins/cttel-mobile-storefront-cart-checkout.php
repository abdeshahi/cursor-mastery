<?php
/**
 * Cart & checkout — mobile commerce UI (staging-safe, uses native WC forms).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

function cttel_ms_is_cart_page(): bool {
	return function_exists( 'is_cart' ) && is_cart() && ! is_order_received_page();
}

function cttel_ms_is_checkout_page(): bool {
	return function_exists( 'is_checkout' ) && is_checkout() && ! is_order_received_page();
}

function cttel_ms_is_commerce_flow_page(): bool {
	return cttel_ms_is_cart_page() || cttel_ms_is_checkout_page();
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_ms_is_cart_page() ) {
			$classes[] = 'cttel-mobile-storefront';
			$classes[] = 'cttel-ms-cart';
		}
		if ( cttel_ms_is_checkout_page() ) {
			$classes[] = 'cttel-mobile-storefront';
			$classes[] = 'cttel-ms-checkout';
		}
		return $classes;
	}
);

/**
 * Prefer classic WooCommerce cart/checkout shortcodes over block templates (native totals, coupons, gateways).
 */
add_filter(
	'the_content',
	static function ( string $content ): string {
		if ( ! cttel_ms_is_commerce_flow_page() ) {
			return $content;
		}
		if ( ! function_exists( 'has_block' ) ) {
			return $content;
		}
		if ( cttel_ms_is_cart_page() && ( has_block( 'woocommerce/cart', $content ) || str_contains( $content, 'woocommerce/cart' ) ) ) {
			return do_shortcode( '[woocommerce_cart]' );
		}
		if ( cttel_ms_is_checkout_page() && ( has_block( 'woocommerce/checkout', $content ) || str_contains( $content, 'woocommerce/checkout' ) ) ) {
			return do_shortcode( '[woocommerce_checkout]' );
		}
		return $content;
	},
	9
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( cttel_ms_is_cart_page() ) {
			wp_enqueue_script( 'wc-cart' );
			wp_add_inline_script(
				'wc-cart',
				"(function ($) {
	function cttelMsPruneDuplicateCartQty() {
		var \$form = $('.woocommerce-cart-form');
		if (!\$form.length || !$('body').hasClass('cttel-ms-cart')) {
			return;
		}
		\$form.find('.product-mobile-actions input.qty').remove();
		\$form.find('tr.cart_item').each(function () {
			var \$qty = $(this).find('td.product-quantity input.qty');
			if (\$qty.length > 1) {
				\$qty.slice(1).remove();
			}
		});
	}
	$(function () {
		cttelMsPruneDuplicateCartQty();
	});
	$(document.body).on('updated_wc_div updated_cart_totals', cttelMsPruneDuplicateCartQty);
})(jQuery);",
				'after'
			);
		}
		if ( ! cttel_ms_is_commerce_flow_page() ) {
			return;
		}
		wp_enqueue_style( 'cttel-design-system' );
		wp_register_style(
			'cttel-mobile-storefront',
			false,
			array( 'cttel-design-system' ),
			defined( 'CTTEL_MOBILE_STOREFRONT_VERSION' ) ? CTTEL_MOBILE_STOREFRONT_VERSION : '1.0.0'
		);
		wp_enqueue_style( 'cttel-mobile-storefront' );
		$css_path = __DIR__ . '/cttel-mobile-storefront.css';
		if ( is_readable( $css_path ) ) {
			wp_add_inline_style( 'cttel-mobile-storefront', (string) file_get_contents( $css_path ) );
		}
	},
	40
);

add_action(
	'woocommerce_before_cart',
	static function (): void {
		if ( ! cttel_ms_is_cart_page() ) {
			return;
		}
		cttel_ms_commerce_render_toolbar( __( 'سبد خرید', 'cttel-store' ) );
	},
	5
);

add_action(
	'woocommerce_before_checkout_form',
	static function (): void {
		if ( ! cttel_ms_is_checkout_page() ) {
			return;
		}
		cttel_ms_commerce_render_toolbar( __( 'تسویه حساب', 'cttel-store' ) );
	},
	5
);

function cttel_ms_commerce_render_toolbar( string $title ): void {
	?>
	<div class="cttel-ms-commerce-head">
		<a class="cttel-ms-commerce-head__back" href="<?php echo esc_url( cttel_mobile_storefront_categories_url() ); ?>">
			<?php echo cttel_mobile_storefront_icon( 'chev', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
			<span><?php esc_html_e( 'بازگشت', 'cttel-store' ); ?></span>
		</a>
		<h1 class="cttel-ms-commerce-head__title"><?php echo esc_html( $title ); ?></h1>
		<span class="cttel-ms-commerce-head__spacer" aria-hidden="true"></span>
	</div>
	<?php
}

add_filter(
	'woocommerce_cart_empty_message',
	static function (): string {
		return cttel_ms_is_cart_page() ? '' : __( 'سبد خرید شما خالی است.', 'woocommerce' );
	}
);

add_action(
	'woocommerce_cart_is_empty',
	static function (): void {
		if ( ! cttel_ms_is_cart_page() ) {
			return;
		}
		$shop = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
		?>
		<div class="cttel-ms-cart-empty">
			<p class="cttel-ms-cart-empty__text"><?php esc_html_e( 'سبد خرید شما خالی است.', 'cttel-store' ); ?></p>
			<a class="cttel-ms-btn cttel-ms-btn--primary" href="<?php echo esc_url( cttel_mobile_storefront_categories_url() ); ?>">
				<?php esc_html_e( 'مشاهده محصولات', 'cttel-store' );
				?>
			</a>
			<a class="cttel-ms-cart-empty__secondary" href="<?php echo esc_url( $shop ); ?>"><?php esc_html_e( 'ادامه خرید', 'cttel-store' ); ?></a>
		</div>
		<?php
	},
	5
);

add_filter(
	'woocommerce_return_to_shop_text',
	static function (): string {
		return __( 'ادامه خرید', 'cttel-store' );
	}
);

add_filter(
	'woocommerce_quantity_input_args',
	static function ( array $args, $product ): array {
		if ( ! cttel_ms_is_cart_page() ) {
			return $args;
		}
		$args['min_value']   = max( 1, (int) ( $args['min_value'] ?? 1 ) );
		$args['input_value'] = max( 1, (int) ( $args['input_value'] ?? 1 ) );
		return $args;
	},
	20,
	2
);

add_filter(
	'woocommerce_proceed_to_checkout_button_text',
	static function (): string {
		return __( 'ادامه جهت تسویه حساب', 'cttel-store' );
	}
);

add_action(
	'wp_footer',
	static function (): void {
		if ( ! cttel_ms_is_commerce_flow_page() ) {
			return;
		}
		cttel_mobile_storefront_render_bottom_nav();
	},
	5
);

add_action(
	'wp',
	static function (): void {
		if ( ! cttel_ms_is_commerce_flow_page() ) {
			return;
		}
		remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );
	},
	20
);

if ( ! function_exists( 'cttel_is_staging_site' ) ) {
	function cttel_is_staging_site(): bool {
		if ( defined( 'CTTEL_STAGING' ) && CTTEL_STAGING ) {
			return true;
		}
		$host = isset( $_SERVER['HTTP_HOST'] ) ? strtolower( (string) $_SERVER['HTTP_HOST'] ) : '';
		return str_contains( $host, 'staging.' ) || str_contains( $host, 'staging.cttel' );
	}
}

add_action(
	'wp_footer',
	static function (): void {
		if ( ! cttel_is_staging_site() || ! cttel_ms_is_checkout_page() ) {
			return;
		}
		$available = function_exists( 'WC' ) ? array_keys( WC()->payment_gateways()->get_available_payment_gateways() ) : array();
		$online    = function_exists( 'cttel_wc_online_gateway_configured' ) && cttel_wc_online_gateway_configured();
		echo '<!-- cttel-ms-checkout online_gateway=' . esc_attr( $online ? '1' : '0' ) . ' available=' . esc_attr( implode( ',', $available ) ) . ' -->';
	},
	999
);
