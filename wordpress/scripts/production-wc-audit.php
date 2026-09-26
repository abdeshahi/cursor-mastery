<?php
/**
 * Read-only production WooCommerce audit (wp eval-file). No writes.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

$report = array(
	'wordpress' => get_bloginfo( 'version' ),
	'woocommerce' => defined( 'WC_VERSION' ) ? WC_VERSION : null,
	'php'         => PHP_VERSION,
	'theme'       => wp_get_theme()->get( 'Name' ) . ' ' . wp_get_theme()->get( 'Version' ),
	'plugins_active' => array(),
	'options'     => array(),
	'gateways'    => array(),
	'shipping_zones' => array(),
	'billing_fields_ir' => array(),
	'health'      => array(),
);

foreach ( get_option( 'active_plugins', array() ) as $plugin ) {
	$data = get_plugin_data( WP_PLUGIN_DIR . '/' . $plugin, false, false );
	$report['plugins_active'][] = array(
		'file'    => $plugin,
		'name'    => $data['Name'] ?? $plugin,
		'version' => $data['Version'] ?? '',
	);
}

$option_keys = array(
	'woocommerce_enable_guest_checkout',
	'woocommerce_enable_checkout_login_reminder',
	'woocommerce_enable_signup_and_login_from_checkout',
	'woocommerce_enable_myaccount_registration',
	'woocommerce_ship_to_destination',
	'woocommerce_calc_taxes',
	'woocommerce_enable_coupons',
);
foreach ( $option_keys as $key ) {
	$report['options'][ $key ] = get_option( $key );
}

if ( function_exists( 'WC' ) && WC()->payment_gateways() ) {
	$available = WC()->payment_gateways()->get_available_payment_gateways();
	foreach ( WC()->payment_gateways()->payment_gateways() as $id => $gw ) {
		$creds = false;
		if ( is_array( $gw->settings ?? null ) ) {
			foreach ( $gw->settings as $k => $v ) {
				if ( ! is_string( $v ) || '' === trim( $v ) ) {
					continue;
				}
				$kl = strtolower( (string) $k );
				if ( preg_match( '/merchant|api_key|apikey|terminal|password|secret|pin|username|salt|key$/', $kl ) ) {
					$creds = true;
					break;
				}
			}
		}
		$plugin_slug = '';
		if ( is_object( $gw ) ) {
			$ref = new ReflectionClass( $gw );
			$file = $ref->getFileName();
			if ( $file && str_contains( $file, '/plugins/' ) ) {
				$plugin_slug = explode( '/plugins/', $file )[1] ?? '';
				$plugin_slug = explode( '/', $plugin_slug )[0] ?? '';
			}
		}
		$report['gateways'][] = array(
			'id'                    => $id,
			'class'                 => is_object( $gw ) ? get_class( $gw ) : '',
			'plugin_slug'           => $plugin_slug,
			'enabled'               => ( $gw->enabled ?? 'no' ) === 'yes' ? 'YES' : 'NO',
			'customer_title'        => method_exists( $gw, 'get_title' ) ? $gw->get_title() : '',
			'available_at_checkout' => isset( $available[ $id ] ) ? 'YES' : 'NO',
			'credentials_present'   => $creds ? 'YES' : 'NO',
			'registered'            => 'YES',
		);
	}
}

$patterns = array( 'zarinpal', 'zarin', 'idpay', 'nextpay', 'zibal', 'payir', 'mellat', 'saman', 'behpardakht', 'pasargad', 'sep', 'sadad', 'parsian', 'iran', 'persian' );
$all_plugins = get_plugins();
$report['payment_related_plugins'] = array();
foreach ( $all_plugins as $file => $meta ) {
	$blob = strtolower( $file . ' ' . ( $meta['Name'] ?? '' ) );
	foreach ( $patterns as $p ) {
		if ( str_contains( $blob, $p ) ) {
			$report['payment_related_plugins'][] = array(
				'file'     => $file,
				'name'     => $meta['Name'] ?? $file,
				'installed' => 'YES',
				'active'   => is_plugin_active( $file ) ? 'YES' : 'NO',
			);
			break;
		}
	}
}

if ( class_exists( 'WC_Shipping_Zones' ) ) {
	foreach ( WC_Shipping_Zones::get_zones() as $zone ) {
		$z     = WC_Shipping_Zones::get_zone( $zone['zone_id'] ?? 0 );
		$entry = array(
			'zone_name' => $zone['zone_name'] ?? '',
			'locations' => array(),
			'methods'   => array(),
		);
		if ( $z ) {
			foreach ( $z->get_zone_locations() as $loc ) {
				$entry['locations'][] = ( $loc->type ?? '' ) . ':' . ( $loc->code ?? '' );
			}
			foreach ( $z->get_shipping_methods( true ) as $m ) {
				$entry['methods'][] = array(
					'method_id'   => $m->id ?? '',
					'instance_id' => $m->instance_id ?? null,
					'enabled'     => ( $m->enabled ?? 'no' ) === 'yes' ? 'YES' : 'NO',
					'title'       => method_exists( $m, 'get_title' ) ? $m->get_title() : '',
					'cost'        => ( 'flat_rate' === ( $m->id ?? '' ) && method_exists( $m, 'get_option' ) ) ? $m->get_option( 'cost', '' ) : null,
				);
			}
		}
		$report['shipping_zones'][] = $entry;
	}
	$rest = WC_Shipping_Zones::get_zone( 0 );
	if ( $rest ) {
		$entry = array( 'zone_name' => 'locations_not_covered_by_other_zones', 'locations' => array(), 'methods' => array() );
		foreach ( $rest->get_shipping_methods( true ) as $m ) {
			$entry['methods'][] = array(
				'method_id'   => $m->id ?? '',
				'instance_id' => $m->instance_id ?? null,
				'enabled'     => ( $m->enabled ?? 'no' ) === 'yes' ? 'YES' : 'NO',
				'title'       => method_exists( $m, 'get_title' ) ? $m->get_title() : '',
				'cost'        => ( 'flat_rate' === ( $m->id ?? '' ) && method_exists( $m, 'get_option' ) ) ? $m->get_option( 'cost', '' ) : null,
			);
		}
		$report['shipping_zones'][] = $entry;
	}
}

if ( function_exists( 'WC' ) ) {
	$fields = WC()->countries->get_address_fields( 'IR', 'billing_' );
	foreach ( $fields as $key => $f ) {
		if ( ! str_starts_with( $key, 'billing_' ) ) {
			continue;
		}
		$short = str_replace( 'billing_', '', $key );
		$report['billing_fields_ir'][ $short ] = ! empty( $f['required'] ) ? 'required' : 'optional';
	}
	$report['billing_fields_ir']['order_notes'] = 'optional';
}

$log = WP_CONTENT_DIR . '/debug.log';
if ( is_readable( $log ) ) {
	$lines = file( $log, FILE_IGNORE_NEW_LINES );
	if ( is_array( $lines ) ) {
		$tail = array_slice( $lines, -200 );
		foreach ( $tail as $line ) {
			if ( ! preg_match( '/fatal|woocommerce|payment|gateway|error/i', $line ) ) {
				continue;
			}
			if ( preg_match( '/(@|password|secret|token|api[_-]?key)/i', $line ) ) {
				continue;
			}
			$report['health'][] = substr( $line, 0, 240 );
		}
		$report['health'] = array_slice( $report['health'], -15 );
	}
}

echo wp_json_encode( $report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
