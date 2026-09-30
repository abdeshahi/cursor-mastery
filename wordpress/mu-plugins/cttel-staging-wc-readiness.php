<?php
/**
 * Staging-only WooCommerce checkout readiness (COD, no production changes).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

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
 * Enable cash-on-delivery on staging when no online gateway is configured (no card charge).
 */
add_action(
	'init',
	static function (): void {
		if ( ! cttel_is_staging_site() || ! function_exists( 'WC' ) ) {
			return;
		}
		$key = 'cttel_staging_cod_bootstrapped_v2';
		if ( get_option( $key ) ) {
			return;
		}

		$cod = get_option( 'woocommerce_cod_settings', array() );
		if ( ! is_array( $cod ) ) {
			$cod = array();
		}
		$cod['enabled']  = 'yes';
		$cod['title']    = $cod['title'] ?? 'پرداخت در محل';
		$cod['description'] = $cod['description'] ?? 'پرداخت نقدی هنگام تحویل (تست استیجینگ).';
		update_option( 'woocommerce_cod_settings', $cod );

		$order = get_option( 'woocommerce_gateway_order', array() );
		if ( ! is_array( $order ) ) {
			$order = array();
		}
		if ( ! in_array( 'cod', $order, true ) ) {
			array_unshift( $order, 'cod' );
			update_option( 'woocommerce_gateway_order', $order );
		}

		update_option( $key, 1 );
	},
	20
);

/** Ensure COD is offered on staging when no online gateway is configured (no card capture). */
add_filter(
	'woocommerce_available_payment_gateways',
	static function ( array $gateways ): array {
		if ( ! cttel_is_staging_site() || ! function_exists( 'WC' ) ) {
			return $gateways;
		}
		if ( isset( $gateways['cod'] ) ) {
			return $gateways;
		}
		$all = WC()->payment_gateways()->payment_gateways();
		if ( isset( $all['cod'] ) ) {
			$all['cod']->enabled            = 'yes';
			$all['cod']->settings['enabled'] = 'yes';
			$gateways['cod']                = $all['cod'];
		}
		return $gateways;
	},
	100
);

add_filter(
	'woocommerce_gateway_cod_is_available',
	static function ( bool $available ): bool {
		return cttel_is_staging_site() ? true : $available;
	}
);

/**
 * @return array<string, mixed>
 */
function cttel_staging_wc_audit_snapshot(): array {
	$out = array(
		'gateways' => array(),
		'shipping' => array(),
	);

	if ( ! function_exists( 'WC' ) ) {
		return $out;
	}

	$manager = WC()->payment_gateways();
	if ( $manager ) {
		foreach ( $manager->payment_gateways() as $id => $gateway ) {
			if ( ! is_object( $gateway ) || ! method_exists( $gateway, 'get_title' ) ) {
				continue;
			}
			$out['gateways'][] = array(
				'id'      => $id,
				'title'   => $gateway->get_title(),
				'enabled' => $gateway->enabled ?? 'no',
				'has_fields' => method_exists( $gateway, 'has_fields' ) ? $gateway->has_fields() : null,
			);
		}
	}

	if ( class_exists( 'WC_Shipping_Zones' ) ) {
		$zones = WC_Shipping_Zones::get_zones();
		foreach ( $zones as $zone ) {
			$methods = array();
			if ( ! empty( $zone['shipping_methods'] ) ) {
				foreach ( $zone['shipping_methods'] as $method ) {
					if ( ! is_object( $method ) ) {
						continue;
					}
					$methods[] = array(
						'id'      => $method->id ?? '',
						'title'   => method_exists( $method, 'get_title' ) ? $method->get_title() : '',
						'enabled' => $method->enabled ?? 'no',
					);
				}
			}
			$out['shipping'][] = array(
				'name'    => $zone['zone_name'] ?? '',
				'order'   => $zone['zone_order'] ?? 0,
				'methods' => $methods,
			);
		}
		$rest = WC_Shipping_Zones::get_zone( 0 );
		if ( $rest ) {
			$methods = array();
			foreach ( $rest->get_shipping_methods( true ) as $method ) {
				$methods[] = array(
					'id'      => $method->id ?? '',
					'title'   => method_exists( $method, 'get_title' ) ? $method->get_title() : '',
					'enabled' => $method->enabled ?? 'no',
				);
			}
			$out['shipping'][] = array(
				'name'    => __( 'سایر مناطق', 'cttel-store' ),
				'order'   => 999,
				'methods' => $methods,
			);
		}
	}

	return $out;
}
