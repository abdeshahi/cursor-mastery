<?php
/**
 * Staging: product payment online-only; shipping postpaid (separate). No COD/BACS/cheque for merchandise.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

const CTTEL_OFFLINE_GATEWAY_IDS           = array( 'cod', 'bacs', 'cheque' );
const CTTEL_DISABLE_OFFLINE_BOOT_KEY      = 'cttel_staging_offline_gateways_disabled_v1';

/**
 * Gateways that count as a real online product payment (excludes offline defaults).
 *
 * @return string[]
 */
function cttel_wc_offline_gateway_ids(): array {
	return CTTEL_OFFLINE_GATEWAY_IDS;
}

/**
 * @return bool
 */
function cttel_wc_online_gateway_configured(): bool {
	if ( ! function_exists( 'WC' ) || ! WC()->payment_gateways() ) {
		return false;
	}
	$offline = cttel_wc_offline_gateway_ids();
	foreach ( WC()->payment_gateways()->payment_gateways() as $id => $gateway ) {
		if ( in_array( $id, $offline, true ) ) {
			continue;
		}
		if ( ! is_object( $gateway ) ) {
			continue;
		}
		if ( 'yes' !== (string) ( $gateway->enabled ?? 'no' ) ) {
			continue;
		}
		if ( method_exists( $gateway, 'is_available' ) && ! $gateway->is_available() ) {
			continue;
		}
		return true;
	}
	return false;
}

/**
 * Persistently disable WooCommerce offline gateways on staging (product = online only).
 */
function cttel_staging_disable_offline_gateways(): void {
	if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
		return;
	}
	foreach ( cttel_wc_offline_gateway_ids() as $gateway_id ) {
		$settings = get_option( 'woocommerce_' . $gateway_id . '_settings', array() );
		if ( ! is_array( $settings ) ) {
			$settings = array();
		}
		if ( ( $settings['enabled'] ?? 'no' ) === 'no' ) {
			continue;
		}
		$settings['enabled'] = 'no';
		update_option( 'woocommerce_' . $gateway_id . '_settings', $settings );
	}
	if ( ! get_option( CTTEL_DISABLE_OFFLINE_BOOT_KEY ) ) {
		update_option( CTTEL_DISABLE_OFFLINE_BOOT_KEY, 1 );
	}
}

add_action( 'init', 'cttel_staging_disable_offline_gateways', 19 );

/**
 * @param array<string, WC_Payment_Gateway> $gateways
 * @return array<string, WC_Payment_Gateway>
 */
function cttel_ms_filter_offline_payment_gateways( array $gateways ): array {
	if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
		return $gateways;
	}
	foreach ( cttel_wc_offline_gateway_ids() as $id ) {
		unset( $gateways[ $id ] );
	}
	return $gateways;
}

add_filter( 'woocommerce_available_payment_gateways', 'cttel_ms_filter_offline_payment_gateways', 5 );

foreach ( cttel_wc_offline_gateway_ids() as $cttel_offline_id ) {
	add_filter(
		'woocommerce_gateway_' . $cttel_offline_id . '_is_available',
		static function ( bool $available ): bool {
			return function_exists( 'cttel_is_staging_site' ) && cttel_is_staging_site() ? false : $available;
		},
		100
	);
}

add_action(
	'woocommerce_before_checkout_form',
	static function (): void {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return;
		}
		if ( ! function_exists( 'cttel_ms_is_checkout_page' ) || ! cttel_ms_is_checkout_page() ) {
			return;
		}
		if ( cttel_wc_online_gateway_configured() ) {
			return;
		}
		wc_print_notice(
			__( 'درگاه پرداخت آنلاین محصول هنوز روی این محیط پیکربندی نشده است. مبلغ کالا باید آنلاین پرداخت شود — پرداخت هنگام تحویل فقط برای هزینه ارسال (پس‌کرایه) است.', 'cttel-store' ),
			'notice'
		);
	},
	12
);

/**
 * Relabel cart/checkout totals (product vs postpaid shipping).
 */
function cttel_ms_commerce_totals_use_custom_labels(): bool {
	if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
		return false;
	}
	return function_exists( 'cttel_ms_is_commerce_flow_page' ) && cttel_ms_is_commerce_flow_page();
}

add_filter(
	'gettext',
	static function ( $translated, $text, $domain ) {
		if ( ! is_string( $translated ) || ! is_string( $text ) || ! is_string( $domain ) ) {
			return $translated;
		}
		if ( ! cttel_ms_commerce_totals_use_custom_labels() || 'woocommerce' !== $domain ) {
			return $translated;
		}
		$map = array(
			'Subtotal'    => 'جمع محصولات',
			'جمع جزء'     => 'جمع محصولات',
			'Shipping'    => 'هزینه ارسال',
			'Total'       => 'مبلغ قابل پرداخت آنلاین',
			'Order total' => 'مبلغ قابل پرداخت آنلاین',
		);
		return $map[ $text ] ?? ( $map[ $translated ] ?? $translated );
	},
	20,
	3
);

add_filter(
	'woocommerce_get_order_item_totals',
	static function ( array $total_rows, $order ): array {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return $total_rows;
		}
		if ( isset( $total_rows['cart_subtotal'] ) ) {
			$total_rows['cart_subtotal']['label'] = __( 'جمع محصولات:', 'cttel-store' );
		}
		if ( isset( $total_rows['shipping'] ) ) {
			$total_rows['shipping']['label'] = __( 'هزینه ارسال:', 'cttel-store' );
			$total_rows['shipping']['value'] = __( 'پس‌کرایه', 'cttel-store' );
		}
		if ( isset( $total_rows['order_total'] ) ) {
			$total_rows['order_total']['label'] = __( 'مبلغ قابل پرداخت آنلاین:', 'cttel-store' );
		}
		return $total_rows;
	},
	20,
	2
);

add_filter(
	'woocommerce_order_button_text',
	static function ( string $text ): string {
		if ( cttel_ms_commerce_totals_use_custom_labels() ) {
			return __( 'پرداخت آنلاین', 'cttel-store' );
		}
		return $text;
	}
);

add_action(
	'woocommerce_thankyou',
	static function ( $order_id ): void {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return;
		}
		if ( ! $order_id ) {
			return;
		}
		$order = wc_get_order( $order_id );
		if ( ! $order instanceof WC_Order || ! $order->is_paid() ) {
			return;
		}
		?>
		<div class="cttel-ms-order-paid-notice" role="status">
			<p><?php esc_html_e( 'پرداخت سفارش با موفقیت انجام شد.', 'cttel-store' ); ?></p>
			<p><?php esc_html_e( 'مرسوله از طریق تیپاکس یا ماهکس ارسال می‌شود و هزینه ارسال هنگام تحویل توسط مشتری پرداخت خواهد شد.', 'cttel-store' ); ?></p>
		</div>
		<?php
	},
	8
);
