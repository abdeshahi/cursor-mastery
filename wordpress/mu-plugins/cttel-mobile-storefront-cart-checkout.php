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
	$(function () {
		var \$form = $('.woocommerce-cart-form');
		if (!\$form.length || !$('body').hasClass('cttel-ms-cart')) {
			return;
		}
		function isMobileCart() {
			return window.matchMedia('(max-width: 999.98px)').matches;
		}
		function activeQtyInput(\$row) {
			if (isMobileCart()) {
				return \$row.find('.product-mobile-actions input.qty').first();
			}
			return \$row.find('td.product-quantity input.qty').first();
		}
		function syncCartQtyInputs() {
			\$form.find('tr.cart_item').each(function () {
				var \$row = $(this);
				var \$primary = activeQtyInput(\$row);
				var \$all = \$row.find('input.qty[name]');
				if (!\$primary.length || \$all.length < 2) {
					return;
				}
				var val = \$primary.val();
				\$all.not(\$primary).prop('disabled', true).val(val);
				\$primary.prop('disabled', false);
			});
		}
		function submitCartUpdate() {
			syncCartQtyInputs();
			var \$btn = \$form.find('[name=\"update_cart\"]');
			if (!\$btn.length) {
				return;
			}
			\$btn.prop('disabled', false).removeAttr('aria-disabled');
			\$btn.trigger('click');
		}
		syncCartQtyInputs();
		$(window).on('resize', syncCartQtyInputs);
		\$form.on('change', 'input.qty', submitCartUpdate);
		\$form.on('click', '.quantity .ct-increase, .quantity .ct-decrease', function () {
			window.setTimeout(submitCartUpdate, 120);
		});
	});
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

/**
 * Staging-only: enable offline gateways for cash/bank test orders (never production).
 */
function cttel_ms_staging_bootstrap_offline_gateways(): void {
	if ( ! cttel_is_staging_site() ) {
		return;
	}
	$key = 'cttel_staging_cod_bootstrapped_v4';
	if ( get_option( $key ) ) {
		return;
	}
	$cod = get_option( 'woocommerce_cod_settings', array() );
	if ( ! is_array( $cod ) ) {
		$cod = array();
	}
	$cod['enabled']            = 'yes';
	$cod['title']              = $cod['title'] ?? 'پرداخت در محل';
	$cod['description']        = $cod['description'] ?? 'پرداخت نقدی هنگام تحویل (استیجینگ).';
	$cod['enable_for_virtual'] = 'yes';
	$cod['enable_for_methods'] = array();
	update_option( 'woocommerce_cod_settings', $cod );

	foreach ( array( 'bacs', 'cheque' ) as $offline_id ) {
		$settings = get_option( 'woocommerce_' . $offline_id . '_settings', array() );
		if ( ! is_array( $settings ) ) {
			$settings = array();
		}
		$settings['enabled'] = 'yes';
		update_option( 'woocommerce_' . $offline_id . '_settings', $settings );
	}

	$order = get_option( 'woocommerce_gateway_order', array() );
	if ( ! is_array( $order ) ) {
		$order = array();
	}
	foreach ( array( 'cod', 'bacs', 'cheque' ) as $gateway_id ) {
		if ( ! in_array( $gateway_id, $order, true ) ) {
			array_unshift( $order, $gateway_id );
		}
	}
	update_option( 'woocommerce_gateway_order', $order );
	update_option( $key, 1 );
}

add_action( 'init', 'cttel_ms_staging_bootstrap_offline_gateways', 20 );

/**
 * Relax COD shipping-method restrictions on staging (DB may still list legacy method IDs).
 */
function cttel_ms_staging_prepare_offline_gateways( WC_Payment_Gateways $manager ): void {
	if ( ! cttel_is_staging_site() ) {
		return;
	}
	foreach ( $manager->payment_gateways() as $gateway_id => $gateway ) {
		if ( ! in_array( $gateway_id, array( 'cod', 'bacs', 'cheque' ), true ) ) {
			continue;
		}
		$gateway->enabled = 'yes';
		if ( is_array( $gateway->settings ) ) {
			$gateway->settings['enabled'] = 'yes';
		}
		if ( 'cod' === $gateway_id && property_exists( $gateway, 'enable_for_methods' ) ) {
			$gateway->enable_for_methods = array();
		}
	}
}

add_action(
	'wc_payment_gateways_initialized',
	static function ( WC_Payment_Gateways $manager ): void {
		cttel_ms_staging_prepare_offline_gateways( $manager );
	}
);

add_filter(
	'woocommerce_available_payment_gateways',
	static function ( array $gateways ): array {
		if ( ! cttel_is_staging_site() || ! function_exists( 'WC' ) || ! WC()->payment_gateways() ) {
			return $gateways;
		}
		if ( ! WC()->cart || WC()->cart->is_empty() ) {
			return $gateways;
		}
		cttel_ms_staging_prepare_offline_gateways( WC()->payment_gateways() );
		$all = WC()->payment_gateways()->payment_gateways();
		foreach ( array( 'cod', 'bacs', 'cheque' ) as $gateway_id ) {
			if ( ! isset( $all[ $gateway_id ] ) || ! is_a( $all[ $gateway_id ], 'WC_Payment_Gateway' ) ) {
				continue;
			}
			$gateways[ $gateway_id ] = $all[ $gateway_id ];
		}
		return $gateways;
	},
	PHP_INT_MAX
);

add_filter(
	'woocommerce_payment_gateways',
	static function ( array $methods ): array {
		if ( ! cttel_is_staging_site() ) {
			return $methods;
		}
		foreach ( array( 'WC_Gateway_COD', 'WC_Gateway_BACS', 'WC_Gateway_Cheque' ) as $class ) {
			if ( ! in_array( $class, $methods, true ) && class_exists( $class ) ) {
				$methods[] = $class;
			}
		}
		return $methods;
	}
);

add_filter(
	'woocommerce_gateway_cod_is_available',
	static function ( bool $available ): bool {
		return cttel_is_staging_site() ? true : $available;
	}
);

add_filter(
	'woocommerce_gateway_bacs_is_available',
	static function ( bool $available ): bool {
		return cttel_is_staging_site() ? true : $available;
	}
);

add_filter(
	'woocommerce_gateway_cheque_is_available',
	static function ( bool $available ): bool {
		return cttel_is_staging_site() ? true : $available;
	}
);

add_action(
	'wp_footer',
	static function (): void {
		if ( ! cttel_is_staging_site() || ! cttel_ms_is_checkout_page() ) {
			return;
		}
		$registered = function_exists( 'WC' ) ? array_keys( WC()->payment_gateways()->payment_gateways() ) : array();
		$available  = function_exists( 'WC' ) ? array_keys( WC()->payment_gateways()->get_available_payment_gateways() ) : array();
		$cod_raw    = '';
		if ( function_exists( 'WC' ) && isset( WC()->payment_gateways()->payment_gateways()['cod'] ) ) {
			$cod_g   = WC()->payment_gateways()->payment_gateways()['cod'];
			$cod_raw = ( $cod_g->is_available() ? '1' : '0' ) . '|' . (string) ( $cod_g->enabled ?? '' );
		}
		echo '<!-- cttel-ms-cart-checkout-v1 registered=' . esc_attr( implode( ',', $registered ) ) . ' available=' . esc_attr( implode( ',', $available ) ) . ' cod=' . esc_attr( $cod_raw ) . ' -->';
	},
	999
);
