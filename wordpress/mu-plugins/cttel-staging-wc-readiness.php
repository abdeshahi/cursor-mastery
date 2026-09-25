<?php
/**
 * Staging-only WooCommerce checkout readiness (COD, no production changes).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

require_once __DIR__ . '/cttel-staging-shipping-postpaid.php';

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

/**
 * Staging-only JSON audit (no production): ?cttel_staging_wc_audit=snapshot
 */
add_action(
	'template_redirect',
	static function (): void {
		if ( ! cttel_is_staging_site() || ! isset( $_GET['cttel_staging_wc_audit'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			return;
		}
		$mode = (string) wp_unslash( $_GET['cttel_staging_wc_audit'] ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		if ( 'snapshot' === $mode ) {
			if ( ! function_exists( 'WC' ) || ! WC()->payment_gateways() ) {
				wp_send_json( array( 'error' => 'woocommerce_unavailable' ), 503 );
			}
			$snap = cttel_staging_wc_audit_snapshot();
			if ( WC()->cart && ! WC()->cart->is_empty() ) {
				$snap['cart'] = array(
					'needs_payment' => WC()->cart->needs_payment(),
					'total'         => WC()->cart->get_total( 'edit' ),
				);
			}
			$snap['available_gateway_ids'] = array_keys( WC()->payment_gateways()->get_available_payment_gateways() );
			wp_send_json( $snap, 200 );
		}
		if ( 'full' === $mode ) {
			wp_send_json( cttel_staging_wc_full_audit(), 200 );
		}
	},
	5
);

/**
 * Trash known staging QA orders once (no production, no other orders).
 */
add_action(
	'init',
	static function (): void {
		if ( ! cttel_is_staging_site() || ! function_exists( 'wc_get_order' ) ) {
			return;
		}
		if ( get_option( 'cttel_staging_orders_136_137_trashed' ) ) {
			return;
		}
		$targets = array( 136, 137 );
		$results = array();
		foreach ( $targets as $order_id ) {
			$order = wc_get_order( $order_id );
			if ( ! $order ) {
				$results[ (string) $order_id ] = 'not_found';
				continue;
			}
			$email = strtolower( (string) $order->get_billing_email() );
			$note  = (string) $order->get_customer_note();
			$safe  = str_contains( $email, 'staging' ) || str_contains( $email, 'cttel.invalid' ) || str_contains( $note, 'STAGING TEST' );
			if ( ! $safe ) {
				$results[ (string) $order_id ] = 'skipped_not_test';
				continue;
			}
			$order->delete( false );
			$results[ (string) $order_id ] = 'trashed';
		}
		update_option( 'cttel_staging_orders_136_137_trashed', $results, false );
	},
	25
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

/**
 * Deep staging audit: shipping rules, classes, Iranian payment plugins (no secrets).
 *
 * @return array<string, mixed>
 */
function cttel_staging_wc_full_audit(): array {
	$out = array(
		'shipping'         => cttel_staging_wc_shipping_audit(),
		'payment_plugins'  => cttel_staging_wc_payment_plugin_audit(),
		'core_gateways'    => cttel_staging_wc_audit_snapshot()['gateways'] ?? array(),
		'test_order_cleanup' => get_option( 'cttel_staging_orders_136_137_trashed', array() ),
	);

	return $out;
}

/**
 * @return array<string, mixed>
 */
function cttel_staging_wc_shipping_audit(): array {
	$audit = array(
		'iran_zone'           => null,
		'other_zones'         => array(),
		'free_shipping_rules' => array(),
		'flat_rate_methods'   => array(),
		'local_pickup'        => array(),
		'shipping_classes'    => array(),
		'product_classes'     => array(),
		'free_shipping_risk'  => false,
		'postpaid_shipping'   => array(
			'configured'  => false,
			'instance_id' => (int) get_option( CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY, 0 ),
			'title'       => function_exists( 'cttel_postpaid_shipping_title' ) ? cttel_postpaid_shipping_title() : '',
		),
	);

	if ( ! class_exists( 'WC_Shipping_Zones' ) ) {
		return $audit;
	}

	$zones = WC_Shipping_Zones::get_zones();
	foreach ( $zones as $zone ) {
		$entry = cttel_staging_wc_format_zone_audit( $zone );
		$name  = (string) ( $zone['zone_name'] ?? '' );
		if ( str_contains( $name, 'ایران' ) || str_contains( strtolower( $name ), 'iran' ) ) {
			$audit['iran_zone'] = $entry;
		} else {
			$audit['other_zones'][] = $entry;
		}
		cttel_staging_wc_collect_method_details( $entry, $audit );
	}

	$rest = WC_Shipping_Zones::get_zone( 0 );
	if ( $rest ) {
		$entry = array(
			'name'    => 'locations_not_covered_by_other_zones',
			'order'   => 999,
			'methods' => array(),
		);
		foreach ( $rest->get_shipping_methods( true ) as $method ) {
			$entry['methods'][] = cttel_staging_wc_format_shipping_method( $method );
		}
		$audit['other_zones'][] = $entry;
		cttel_staging_wc_collect_method_details( $entry, $audit );
	}

	if ( is_array( $audit['iran_zone'] ) ) {
		foreach ( $audit['iran_zone']['methods'] as $method ) {
			if ( 'free_shipping' === ( $method['id'] ?? '' ) && 'yes' === ( $method['enabled'] ?? 'no' ) ) {
				$requires = (string) ( $method['requires'] ?? '' );
				if ( '' === $requires || 'no' === $requires ) {
					$audit['free_shipping_risk'] = true;
				}
			}
			if ( 'flat_rate' === ( $method['id'] ?? '' ) && 'yes' === ( $method['enabled'] ?? 'no' ) ) {
				$title = (string) ( $method['title'] ?? '' );
				$cost  = (string) ( $method['cost'] ?? '' );
				$inst  = (int) ( $method['instance_id'] ?? 0 );
				$is_postpaid = str_contains( $title, 'پس‌کرایه' )
					|| str_contains( $title, 'تیپاکس' )
					|| ( $inst > 0 && $inst === (int) get_option( CTTEL_POSTPAID_SHIPPING_INSTANCE_KEY, 0 ) && '0' === $cost );
				if ( $is_postpaid ) {
					$audit['postpaid_shipping']['configured'] = true;
					$audit['postpaid_shipping']['title']      = $title;
					$audit['postpaid_shipping']['cost']       = $cost;
				}
			}
		}
	}

	if ( taxonomy_exists( 'product_shipping_class' ) ) {
		$terms = get_terms(
			array(
				'taxonomy'   => 'product_shipping_class',
				'hide_empty' => false,
			)
		);
		if ( is_array( $terms ) ) {
			foreach ( $terms as $term ) {
				if ( $term instanceof WP_Term ) {
					$audit['shipping_classes'][] = array(
						'slug'  => $term->slug,
						'name'  => $term->name,
						'count' => (int) $term->count,
					);
				}
			}
		}
	}

	if ( function_exists( 'wc_get_products' ) ) {
		$products = wc_get_products(
			array(
				'limit'  => 50,
				'return' => 'ids',
			)
		);
		foreach ( $products as $pid ) {
			$product = wc_get_product( $pid );
			if ( ! $product ) {
				continue;
			}
			$class_id = $product->get_shipping_class_id();
			if ( $class_id > 0 ) {
				$term = get_term( $class_id, 'product_shipping_class' );
				$audit['product_classes'][] = array(
					'product_id' => $pid,
					'sku'        => $product->get_sku(),
					'class'      => $term instanceof WP_Term ? $term->name : (string) $class_id,
				);
			}
		}
	}

	return $audit;
}

/**
 * @param array<string, mixed> $zone
 * @return array<string, mixed>
 */
function cttel_staging_wc_format_zone_audit( array $zone ): array {
	$methods = array();
	if ( ! empty( $zone['shipping_methods'] ) ) {
		foreach ( $zone['shipping_methods'] as $method ) {
			if ( is_object( $method ) ) {
				$methods[] = cttel_staging_wc_format_shipping_method( $method );
			}
		}
	}
	return array(
		'name'    => $zone['zone_name'] ?? '',
		'order'   => $zone['zone_order'] ?? 0,
		'methods' => $methods,
	);
}

/**
 * @param object $method Shipping method instance.
 * @return array<string, mixed>
 */
function cttel_staging_wc_format_shipping_method( $method ): array {
	$data = array(
		'id'      => $method->id ?? '',
		'instance_id' => $method->instance_id ?? null,
		'title'   => method_exists( $method, 'get_title' ) ? $method->get_title() : '',
		'enabled' => $method->enabled ?? 'no',
	);

	if ( 'free_shipping' === $data['id'] && method_exists( $method, 'get_option' ) ) {
		$data['requires']   = $method->get_option( 'requires', '' );
		$data['min_amount'] = $method->get_option( 'min_amount', '' );
	}

	if ( 'flat_rate' === $data['id'] && method_exists( $method, 'get_option' ) ) {
		$data['cost'] = $method->get_option( 'cost', '' );
	}

	return $data;
}

/**
 * @param array<string, mixed> $zone_entry Zone audit row.
 * @param array<string, mixed> $audit      Mutable audit bucket.
 */
function cttel_staging_wc_collect_method_details( array $zone_entry, array &$audit ): void {
	foreach ( $zone_entry['methods'] as $method ) {
		if ( 'free_shipping' === ( $method['id'] ?? '' ) ) {
			$audit['free_shipping_rules'][] = array(
				'zone'       => $zone_entry['name'],
				'title'      => $method['title'] ?? '',
				'enabled'    => $method['enabled'] ?? 'no',
				'requires'   => $method['requires'] ?? '',
				'min_amount' => $method['min_amount'] ?? '',
			);
		}
		if ( 'flat_rate' === ( $method['id'] ?? '' ) ) {
			$audit['flat_rate_methods'][] = array(
				'zone'  => $zone_entry['name'],
				'title' => $method['title'] ?? '',
				'cost'  => $method['cost'] ?? '',
			);
		}
		if ( 'local_pickup' === ( $method['id'] ?? '' ) ) {
			$audit['local_pickup'][] = array(
				'zone'    => $zone_entry['name'],
				'title'   => $method['title'] ?? '',
				'enabled' => $method['enabled'] ?? 'no',
			);
		}
	}
}

/**
 * @return array<int, array<string, mixed>>
 */
function cttel_staging_wc_payment_plugin_audit(): array {
	if ( ! function_exists( 'get_plugins' ) ) {
		require_once ABSPATH . 'wp-admin/includes/plugin.php';
	}

	$patterns = array(
		'zarinpal', 'zarin', 'idpay', 'nextpay', 'zibal', 'payir', 'pay.ir',
		'mellat', 'saman', 'pasargad', 'sep', 'sadad', 'behpardakht', 'parsian',
		'iran', 'persian', 'woocommerce-gateway', 'wc-gateway', 'payment',
	);

	$all     = get_plugins();
	$matches = array();

	foreach ( $all as $plugin_file => $meta ) {
		$blob = strtolower( $plugin_file . ' ' . ( $meta['Name'] ?? '' ) . ' ' . ( $meta['Description'] ?? '' ) );
		$hit  = false;
		foreach ( $patterns as $pattern ) {
			if ( str_contains( $blob, $pattern ) ) {
				$hit = true;
				break;
			}
		}
		if ( ! $hit ) {
			continue;
		}
		$active = is_plugin_active( $plugin_file );
		$entry  = array(
			'plugin_name'    => $meta['Name'] ?? $plugin_file,
			'plugin_version' => $meta['Version'] ?? '',
			'plugin_status'  => $active ? 'active' : 'inactive',
			'plugin_file'    => $plugin_file,
			'gateway_name'   => '',
			'sandbox'        => null,
			'credentials_present' => false,
			'safe_to_test'   => false,
		);

		cttel_staging_wc_enrich_payment_plugin_entry( $entry, $plugin_file, $active );
		$matches[] = $entry;
	}

	if ( empty( $matches ) && function_exists( 'WC' ) && WC()->payment_gateways() ) {
		foreach ( WC()->payment_gateways()->payment_gateways() as $id => $gateway ) {
			if ( in_array( $id, array( 'cod', 'bacs', 'cheque', 'paypal' ), true ) ) {
				continue;
			}
			$matches[] = array(
				'plugin_name'         => 'woocommerce_core_gateway',
				'plugin_version'      => defined( 'WC_VERSION' ) ? WC_VERSION : '',
				'plugin_status'       => 'active',
				'gateway_name'        => $id,
				'sandbox'             => null,
				'credentials_present' => 'yes' === ( $gateway->enabled ?? 'no' ),
				'safe_to_test'        => false,
			);
		}
	}

	return $matches;
}

/**
 * @param array<string, mixed> $entry Plugin audit row.
 */
function cttel_staging_wc_enrich_payment_plugin_entry( array &$entry, string $plugin_file, bool $active ): void {
	$slug = dirname( $plugin_file );
	if ( '.' === $slug ) {
		$slug = basename( $plugin_file, '.php' );
	}
	$entry['gateway_name'] = $slug;

	$option_keys = array(
		'woocommerce_' . $slug . '_settings',
		$slug . '_settings',
		'woocommerce_ir_gateway_settings',
	);
	foreach ( $option_keys as $key ) {
		$settings = get_option( $key );
		if ( ! is_array( $settings ) ) {
			continue;
		}
		$entry['credentials_present'] = cttel_staging_wc_settings_have_secrets( $settings );
		$entry['sandbox']             = cttel_staging_wc_detect_sandbox_flag( $settings );
		break;
	}

	$entry['safe_to_test'] = $active && ( true === $entry['sandbox'] || 'yes' === $entry['sandbox'] || 'sandbox' === $entry['sandbox'] );
}

/**
 * @param array<string, mixed> $settings Gateway settings.
 */
function cttel_staging_wc_settings_have_secrets( array $settings ): bool {
	$needles = array( 'merchant', 'api_key', 'apikey', 'terminal', 'password', 'secret', 'pin', 'username' );
	foreach ( $settings as $key => $value ) {
		if ( ! is_string( $value ) || '' === trim( $value ) ) {
			continue;
		}
		$k = strtolower( (string) $key );
		foreach ( $needles as $needle ) {
			if ( str_contains( $k, $needle ) ) {
				return true;
			}
		}
	}
	return false;
}

/**
 * @param array<string, mixed> $settings Gateway settings.
 * @return string|bool|null
 */
function cttel_staging_wc_detect_sandbox_flag( array $settings ) {
	foreach ( $settings as $key => $value ) {
		$k = strtolower( (string) $key );
		if ( str_contains( $k, 'sandbox' ) || str_contains( $k, 'testmode' ) || str_contains( $k, 'test_mode' ) ) {
			return is_string( $value ) ? $value : (bool) $value;
		}
	}
	return null;
}
