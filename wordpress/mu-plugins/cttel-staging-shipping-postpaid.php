<?php
/**
 * Staging-only: Iran postpaid shipping (TIPAX/MAHEX) — 0 تومان in WC, not "free shipping".
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

const CTTEL_POSTPAID_SHIPPING_VERSION     = '1.0.1';
const CTTEL_POSTPAID_SHIPPING_BOOT_KEY      = 'cttel_staging_iran_postpaid_shipping_version';
const CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY  = 'cttel_staging_postpaid_flat_rate_instance_id';

/**
 * @return string
 */
function cttel_postpaid_shipping_title(): string {
	return 'ارسال با تیپاکس / ماهکس — پس‌کرایه';
}

/**
 * @return string
 */
function cttel_postpaid_shipping_description(): string {
	return 'مبلغ کالا به‌صورت آنلاین هنگام ثبت سفارش پرداخت می‌شود. هزینه ارسال در مبلغ سفارش محاسبه نمی‌شود و هنگام تحویل مرسوله، توسط مشتری به شرکت حمل‌ونقل پرداخت خواهد شد.';
}

/**
 * @return string
 */
function cttel_postpaid_shipping_cost_display(): string {
	return 'پس‌کرایه';
}

/**
 * @return WC_Shipping_Zone|null
 */
function cttel_staging_get_iran_shipping_zone() {
	if ( ! class_exists( 'WC_Shipping_Zones' ) ) {
		return null;
	}
	foreach ( WC_Shipping_Zones::get_zones() as $z ) {
		$name = (string) ( $z['zone_name'] ?? '' );
		if ( str_contains( $name, 'ایران' ) || false !== stripos( $name, 'iran' ) ) {
			return new WC_Shipping_Zone( (int) ( $z['zone_id'] ?? 0 ) );
		}
	}
	foreach ( WC_Shipping_Zones::get_zones() as $z ) {
		$zone = new WC_Shipping_Zone( (int) ( $z['zone_id'] ?? 0 ) );
		foreach ( $zone->get_zone_locations() as $loc ) {
			if ( 'country' === ( $loc->type ?? '' ) && 'IR' === ( $loc->code ?? '' ) ) {
				return $zone;
			}
		}
	}
	return null;
}

/**
 * @param int $instance_id Flat rate instance id.
 */
function cttel_staging_save_postpaid_flat_rate_settings( int $instance_id ): void {
	if ( $instance_id <= 0 ) {
		return;
	}
	$key      = 'woocommerce_flat_rate_' . $instance_id . '_settings';
	$settings = get_option( $key, array() );
	if ( ! is_array( $settings ) ) {
		$settings = array();
	}
	$settings['title']      = cttel_postpaid_shipping_title();
	$settings['cost']       = '0';
	$settings['tax_status'] = 'none';
	update_option( $key, $settings );

	if ( class_exists( 'WC_Shipping_Zones' ) ) {
		$method = WC_Shipping_Zones::get_shipping_method( $instance_id );
		if ( $method && method_exists( $method, 'update_option' ) ) {
			$method->update_option( 'title', cttel_postpaid_shipping_title() );
			$method->update_option( 'cost', '0' );
			$method->update_option( 'tax_status', 'none' );
		}
		if ( $method && property_exists( $method, 'enabled' ) ) {
			$method->enabled = 'yes';
		}
	}
}

/**
 * Configure Iran zone: remove free_shipping, ensure flat_rate postpaid (cost 0).
 */
function cttel_staging_bootstrap_iran_postpaid_shipping(): void {
	if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
		return;
	}
	if ( ! class_exists( 'WC_Shipping_Zones' ) ) {
		return;
	}
	if ( CTTEL_POSTPAID_SHIPPING_VERSION === get_option( CTTEL_POSTPAID_SHIPPING_BOOT_KEY, '' ) ) {
		return;
	}

	$zone = cttel_staging_get_iran_shipping_zone();
	if ( ! $zone instanceof WC_Shipping_Zone ) {
		return;
	}

	$postpaid_instance = (int) get_option( CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY, 0 );
	$found_postpaid    = false;

	foreach ( $zone->get_shipping_methods( false ) as $method ) {
		if ( ! is_object( $method ) ) {
			continue;
		}
		$instance_id = (int) ( $method->instance_id ?? 0 );
		$method_id   = (string) ( $method->id ?? '' );

		if ( 'free_shipping' === $method_id && $instance_id > 0 ) {
			$zone->delete_shipping_method( $instance_id );
			continue;
		}

		if ( 'flat_rate' === $method_id && ( $instance_id === $postpaid_instance || $postpaid_instance <= 0 ) ) {
			cttel_staging_save_postpaid_flat_rate_settings( $instance_id );
			update_option( CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY, $instance_id, false );
			$found_postpaid    = true;
			$postpaid_instance = $instance_id;
			break;
		}
	}

	if ( ! $found_postpaid ) {
		$new_id = (int) $zone->add_shipping_method( 'flat_rate' );
		if ( $new_id > 0 ) {
			cttel_staging_save_postpaid_flat_rate_settings( $new_id );
			update_option( CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY, $new_id, false );
		}
	} elseif ( $postpaid_instance > 0 ) {
		cttel_staging_save_postpaid_flat_rate_settings( $postpaid_instance );
	}

	update_option( CTTEL_POSTPAID_SHIPPING_BOOT_KEY, CTTEL_POSTPAID_SHIPPING_VERSION, false );
}

add_action( 'init', 'cttel_staging_bootstrap_iran_postpaid_shipping', 22 );

/**
 * @param WC_Shipping_Rate|object $rate
 */
function cttel_shipping_rate_is_postpaid( $rate ): bool {
	if ( ! is_object( $rate ) ) {
		return false;
	}
	$instance = (int) get_option( CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY, 0 );
	$method   = (string) ( $rate->method_id ?? '' );
	$inst     = (int) ( $rate->instance_id ?? 0 );
	if ( 'flat_rate' === $method && $instance > 0 && $inst === $instance ) {
		return true;
	}
	$label = (string) ( $rate->get_label() ?? $rate->label ?? '' );
	return 'flat_rate' === $method && str_contains( $label, 'پس‌کرایه' );
}

/**
 * Runtime: never offer free_shipping on staging (DB cleanup may lag).
 *
 * @param array<string, WC_Shipping_Rate> $rates
 * @return array<string, WC_Shipping_Rate>
 */
function cttel_staging_filter_package_rates( array $rates ): array {
	foreach ( $rates as $key => $rate ) {
		if ( ! is_object( $rate ) ) {
			continue;
		}
		if ( 'free_shipping' === ( $rate->method_id ?? '' ) ) {
			unset( $rates[ $key ] );
			continue;
		}
		if ( cttel_shipping_rate_is_postpaid( $rate ) ) {
			$rate->label = cttel_postpaid_shipping_title();
			$rate->cost  = 0;
		}
	}
	return $rates;
}

add_filter(
	'woocommerce_package_rates',
	static function ( array $rates ): array {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return $rates;
		}
		return cttel_staging_filter_package_rates( $rates );
	},
	100
);

add_filter(
	'woocommerce_cart_shipping_method_full_label',
	static function ( string $label, $method ): string {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return $label;
		}
		if ( ! cttel_shipping_rate_is_postpaid( $method ) ) {
			return $label;
		}
		return cttel_postpaid_shipping_cost_display();
	},
	20,
	2
);

add_filter(
	'woocommerce_order_shipping_to_display',
	static function ( string $shipping, $order, $tax_display ): string {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return $shipping;
		}
		if ( ! $order instanceof WC_Order ) {
			return $shipping;
		}
		foreach ( $order->get_shipping_methods() as $item ) {
			$name = (string) $item->get_name();
			if ( str_contains( $name, 'پس‌کرایه' ) || str_contains( $name, 'تیپاکس' ) ) {
				return cttel_postpaid_shipping_title() . ' — ' . cttel_postpaid_shipping_cost_display();
			}
		}
		return $shipping;
	},
	20,
	3
);

function cttel_ms_render_postpaid_shipping_notice(): void {
	if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
		return;
	}
	if ( ! function_exists( 'WC' ) || ! WC()->cart || WC()->cart->is_empty() ) {
		return;
	}
	if ( ! WC()->cart->needs_shipping() ) {
		return;
	}
	?>
	<div class="cttel-ms-postpaid-shipping-notice" role="note">
		<p class="cttel-ms-postpaid-shipping-notice__title"><?php echo esc_html( cttel_postpaid_shipping_title() ); ?></p>
		<p class="cttel-ms-postpaid-shipping-notice__text"><?php echo esc_html( cttel_postpaid_shipping_description() ); ?></p>
	</div>
	<?php
}

add_action( 'woocommerce_cart_totals_before_shipping', 'cttel_ms_render_postpaid_shipping_notice', 8 );
add_action( 'woocommerce_review_order_before_shipping', 'cttel_ms_render_postpaid_shipping_notice', 8 );
