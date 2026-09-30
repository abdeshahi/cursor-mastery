<?php
/**
 * Staging: configure ZarinPal WooCommerce gateway (non-secret fields only). No credential writes.
 *
 * Usage: wp eval-file configure-staging-zarinpal-nonsecrets.php --allow-root
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

$plugin_file = 'zarinpal-woocommerce-payment-gateway/index.php';
$report      = array(
	'wordpress' => get_bloginfo( 'version' ),
	'woocommerce' => defined( 'WC_VERSION' ) ? WC_VERSION : null,
	'php'         => PHP_VERSION,
	'plugin'      => array(
		'slug'    => 'zarinpal-woocommerce-payment-gateway',
		'installed' => file_exists( WP_PLUGIN_DIR . '/zarinpal-woocommerce-payment-gateway/index.php' ),
		'active'  => is_plugin_active( $plugin_file ),
		'version' => null,
	),
	'gateway'     => array(
		'id'                   => 'WC_ZPal',
		'registered'           => false,
		'enabled'              => 'no',
		'sandbox'              => 'no',
		'merchant_configured'  => false,
		'access_token_present' => false,
		'callback_base_url'    => null,
		'callback_example'     => null,
	),
	'offline_gateways' => array(),
	'configured'       => false,
);

if ( function_exists( 'get_plugin_data' ) && $report['plugin']['installed'] ) {
	$data = get_plugin_data( WP_PLUGIN_DIR . '/zarinpal-woocommerce-payment-gateway/index.php', false, false );
	$report['plugin']['version'] = $data['Version'] ?? null;
}

if ( ! $report['plugin']['installed'] ) {
	echo wp_json_encode( $report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
	return;
}

$option_key = 'woocommerce_WC_ZPal_settings';
$settings   = get_option( $option_key, array() );
if ( ! is_array( $settings ) ) {
	$settings = array();
}

$settings['title']       = 'پرداخت امن زرین‌پال';
$settings['description'] = 'پرداخت آنلاین مبلغ کالا از طریق درگاه زرین‌پال (شتاب). هزینه ارسال جداگانه و پس‌کرایه است.';
$settings['sandbox']     = 'yes';
$settings['fee_payer']    = 'merchant';
$settings['success_message'] = $settings['success_message'] ?? 'با تشکر از شما. سفارش شما با موفقیت پرداخت شد.';
$settings['failed_message']  = $settings['failed_message'] ?? 'پرداخت شما ناموفق بوده است. لطفاً مجدداً تلاش نمایید.';
// Merchant ID and access_token intentionally not set here (owner via WP Admin only).
// Only normalize the owner-entered merchant ID: strip whitespace and invisible marks
// (e.g. RTL marks from mobile paste). Saved only if the result is a 36-char UUID; never printed.
$report['gateway']['merchant_format'] = 'missing';
$raw_merchant = (string) ( $settings['merchantcode'] ?? '' );
if ( '' !== $raw_merchant ) {
	$clean_merchant = (string) preg_replace( '/[\s\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2066}-\x{2069}\x{FEFF}\x{00A0}]+/u', '', $raw_merchant );
	$is_uuid        = 1 === preg_match( '/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $clean_merchant );
	if ( $is_uuid && $clean_merchant !== $raw_merchant ) {
		$settings['merchantcode']              = $clean_merchant;
		$report['gateway']['merchant_format'] = 'cleaned_valid_uuid';
	} elseif ( $is_uuid ) {
		$report['gateway']['merchant_format'] = 'valid_uuid';
	} else {
		$report['gateway']['merchant_format'] = 'invalid_after_cleanup_length_' . strlen( $clean_merchant );
	}
}

if ( empty( trim( (string) ( $settings['merchantcode'] ?? '' ) ) ) ) {
	$settings['enabled'] = 'no';
} else {
	$settings['enabled'] = 'yes';
}

update_option( $option_key, $settings );
$report['configured'] = true;

foreach ( array( 'cod', 'bacs', 'cheque' ) as $gid ) {
	$gsettings = get_option( 'woocommerce_' . $gid . '_settings', array() );
	$report['offline_gateways'][ $gid ] = is_array( $gsettings ) ? ( $gsettings['enabled'] ?? 'no' ) : 'unknown';
}

if ( function_exists( 'WC' ) && WC()->payment_gateways() ) {
	$gateways = WC()->payment_gateways()->payment_gateways();
	$report['gateway']['registered'] = isset( $gateways['WC_ZPal'] );
	if ( isset( $gateways['WC_ZPal'] ) && is_object( $gateways['WC_ZPal'] ) ) {
		$gw = $gateways['WC_ZPal'];
		$report['gateway']['enabled'] = (string) ( $gw->enabled ?? 'no' );
	}
}

$fresh = get_option( $option_key, array() );
if ( is_array( $fresh ) ) {
	$report['gateway']['enabled']             = (string) ( $fresh['enabled'] ?? 'no' );
	$report['gateway']['sandbox']             = (string) ( $fresh['sandbox'] ?? 'no' );
	$merchant                                   = trim( (string) ( $fresh['merchantcode'] ?? '' ) );
	$report['gateway']['merchant_configured']   = '' !== $merchant;
	$report['gateway']['access_token_present'] = '' !== trim( (string) ( $fresh['access_token'] ?? '' ) );
}

if ( function_exists( 'WC' ) && is_callable( array( WC(), 'api_request_url' ) ) ) {
	$base = WC()->api_request_url( 'WC_ZPal' );
	$report['gateway']['callback_base_url'] = $base;
	$report['gateway']['callback_example']  = add_query_arg( 'wc_order', 'ORDER_ID', $base );
}

// Diagnostics for "invalid payment method" at checkout: why WC_ZPal may be unavailable.
// Plugin source lines only; never gateway settings values.
$report['diagnostics'] = array(
	'store_currency'        => function_exists( 'get_woocommerce_currency' ) ? get_woocommerce_currency() : null,
	'gateway_is_available'  => null,
	'available_gateway_ids' => array(),
	'plugin_conditions'     => array(),
);
if ( function_exists( 'WC' ) && WC()->payment_gateways() ) {
	$gateways = WC()->payment_gateways()->payment_gateways();
	if ( isset( $gateways['WC_ZPal'] ) && method_exists( $gateways['WC_ZPal'], 'is_available' ) ) {
		$report['diagnostics']['gateway_is_available'] = (bool) $gateways['WC_ZPal']->is_available();
		$report['diagnostics']['sandbox_field_defined'] = isset( $gateways['WC_ZPal']->get_form_fields()['sandbox'] );
	}
	$report['diagnostics']['available_gateway_ids'] = array_keys( WC()->payment_gateways()->get_available_payment_gateways() );
}
// Every callback on the availability filter, with its source file (names only).
$report['diagnostics']['available_gateways_filters'] = array();
global $wp_filter;
if ( isset( $wp_filter['woocommerce_available_payment_gateways'] ) ) {
	foreach ( $wp_filter['woocommerce_available_payment_gateways']->callbacks as $priority => $callbacks ) {
		foreach ( $callbacks as $cb ) {
			$fn   = $cb['function'];
			$desc = 'unknown';
			try {
				if ( is_string( $fn ) && function_exists( $fn ) ) {
					$ref = new ReflectionFunction( $fn );
				} elseif ( $fn instanceof Closure ) {
					$ref = new ReflectionFunction( $fn );
				} elseif ( is_array( $fn ) ) {
					$ref = new ReflectionMethod( $fn[0], $fn[1] );
				}
				if ( isset( $ref ) ) {
					$desc = str_replace( ABSPATH, '', (string) $ref->getFileName() ) . ':' . $ref->getStartLine();
					unset( $ref );
				}
			} catch ( ReflectionException $e ) {
				$desc = 'reflection_failed';
			}
			$report['diagnostics']['available_gateways_filters'][] = $priority . ' ' . $desc;
		}
	}
}
$report['diagnostics']['mu_plugins']     = array_map( 'basename', glob( WPMU_PLUGIN_DIR . '/*.php' ) ?: array() );
$report['diagnostics']['active_plugins'] = array_values( (array) get_option( 'active_plugins', array() ) );

// Server-only staging guard (not in the repo): show its source, masking anything secret-looking.
$guard_file = WPMU_PLUGIN_DIR . '/zz-cttel-staging-guard.php';
if ( is_readable( $guard_file ) ) {
	$report['diagnostics']['staging_guard_source'] = array();
	foreach ( array_slice( file( $guard_file ), 0, 150 ) as $n => $line ) {
		if ( preg_match( '/pass|secret|token|merchant|api[_-]?key|auth/i', $line ) && preg_match( '/[\'"][^\'"]{12,}[\'"]/', $line ) ) {
			$line = '[masked: possible secret]';
		}
		$report['diagnostics']['staging_guard_source'][] = ( $n + 1 ) . ': ' . rtrim( $line );
	}
}

$plugin_dir = WP_PLUGIN_DIR . '/zarinpal-woocommerce-payment-gateway';
if ( is_dir( $plugin_dir ) ) {
	$iterator = new RecursiveIteratorIterator( new RecursiveDirectoryIterator( $plugin_dir, FilesystemIterator::SKIP_DOTS ) );
	foreach ( $iterator as $file ) {
		if ( 'php' !== $file->getExtension() ) {
			continue;
		}
		foreach ( file( $file->getPathname() ) as $n => $line ) {
			if ( preg_match( '/is_available|available_payment_gateways|get_woocommerce_currency|\bIR[RT]\b|IRH[RT]/', $line ) ) {
				$report['diagnostics']['plugin_conditions'][] = substr( $file->getPathname(), strlen( $plugin_dir ) + 1 ) . ':' . ( $n + 1 ) . ': ' . substr( trim( $line ), 0, 200 );
			}
		}
	}
	$report['diagnostics']['plugin_conditions'] = array_slice( $report['diagnostics']['plugin_conditions'], 0, 60 );

	// How the plugin sends the customer to ZarinPal (endpoints / redirect / receipt page).
	$report['diagnostics']['plugin_redirect_flow'] = array();
	foreach ( $iterator as $file ) {
		if ( 'php' !== $file->getExtension() ) {
			continue;
		}
		foreach ( file( $file->getPathname() ) as $n => $line ) {
			if ( preg_match( '/receipt_page|woocommerce_receipt_|zarinpal\.com|StartPay|wp_redirect|window\.location|sandbox|process_payment|redirect\'\s*=>/i', $line ) ) {
				$report['diagnostics']['plugin_redirect_flow'][] = substr( $file->getPathname(), strlen( $plugin_dir ) + 1 ) . ':' . ( $n + 1 ) . ': ' . substr( trim( $line ), 0, 200 );
			}
		}
	}
	$report['diagnostics']['plugin_redirect_flow'] = array_slice( $report['diagnostics']['plugin_redirect_flow'], 0, 80 );

	// Source of the receipt-page handler that should send the customer to ZarinPal.
	$gateway_file = $plugin_dir . '/class-wc-gateway-zarinpal.php';
	if ( is_readable( $gateway_file ) ) {
		$lines = file( $gateway_file );
		foreach ( $lines as $n => $line ) {
			if ( false !== strpos( $line, 'function Send_to_ZarinPal_Gateway' ) ) {
				$report['diagnostics']['send_to_gateway_source'] = array();
				foreach ( array_slice( $lines, $n + 105, 110, true ) as $m => $src ) {
					$report['diagnostics']['send_to_gateway_source'][] = ( $m + 1 ) . ': ' . substr( rtrim( $src ), 0, 220 );
				}
				break;
			}
		}
	}
}
$report['diagnostics']['php_output_buffering'] = ini_get( 'output_buffering' );

// Helper's requestPayment() source (how the API call is built and when it throws).
$helper_file = WP_PLUGIN_DIR . '/zarinpal-woocommerce-payment-gateway/ZarinpalHelperClass.php';
if ( is_readable( $helper_file ) ) {
	$lines = file( $helper_file );
	foreach ( $lines as $n => $line ) {
		if ( false !== strpos( $line, 'function requestPayment' ) ) {
			$report['diagnostics']['request_payment_source'] = array();
			foreach ( array_slice( $lines, $n, 70, true ) as $m => $src ) {
				$report['diagnostics']['request_payment_source'][] = ( $m + 1 ) . ': ' . substr( rtrim( $src ), 0, 220 );
			}
			break;
		}
	}
}

// Sandbox-only test request (no money moves): capture ZarinPal's answer or error message.
$report['diagnostics']['sandbox_request_test'] = 'skipped';
if ( function_exists( 'WC' ) && WC()->payment_gateways() ) {
	$gws = WC()->payment_gateways()->payment_gateways();
	$gw  = $gws['WC_ZPal'] ?? null;
	if ( $gw && 'yes' === $gw->get_option( 'sandbox', 'no' ) ) {
		try {
			$prop = new ReflectionProperty( $gw, 'zarinpal' );
			$prop->setAccessible( true );
			$helper    = $prop->getValue( $gw );
			$authority = $helper->requestPayment(
				10000,
				add_query_arg( 'wc_order', 0, WC()->api_request_url( 'WC_ZPal' ) ),
				'CTTEL staging diagnostic',
				array( 'mobile' => '09120000000', 'email' => 'staging@cttel.invalid' ),
				wp_json_encode( array( 'items' => array(), 'discount' => 0, 'total' => 1000 ) ),
				null
			);
			$report['diagnostics']['sandbox_request_test'] = array(
				'ok'               => true,
				'authority_length' => is_string( $authority ) ? strlen( $authority ) : gettype( $authority ),
			);
		} catch ( Throwable $e ) {
			$report['diagnostics']['sandbox_request_test'] = array(
				'ok'    => false,
				'class' => get_class( $e ),
				'error' => substr( $e->getMessage(), 0, 500 ),
			);
		}
	} else {
		$report['diagnostics']['sandbox_request_test'] = 'skipped: sandbox is not on';
	}
}

// Latest ZarinPal orders: status and plugin notes only (no customer data).
$report['diagnostics']['recent_zarinpal_orders'] = array();
if ( function_exists( 'wc_get_orders' ) ) {
	foreach ( wc_get_orders( array( 'payment_method' => 'WC_ZPal', 'limit' => 3, 'orderby' => 'date', 'order' => 'DESC' ) ) as $order ) {
		$notes = array();
		foreach ( wc_get_order_notes( array( 'order_id' => $order->get_id(), 'limit' => 10 ) ) as $note ) {
			$notes[] = substr( wp_strip_all_tags( (string) $note->content ), 0, 300 );
		}
		$report['diagnostics']['recent_zarinpal_orders'][] = array(
			'id'     => $order->get_id(),
			'status' => $order->get_status(),
			'total'  => $order->get_total(),
			'notes'  => $notes,
		);
	}
}

// Can the server reach ZarinPal sandbox? (HTTP status only.)
$report['diagnostics']['sandbox_reachability'] = array();
foreach ( array( 'https://sandbox.zarinpal.com/', 'https://payment.zarinpal.com/' ) as $probe ) {
	$res = wp_remote_get( $probe, array( 'timeout' => 15, 'redirection' => 0 ) );
	$report['diagnostics']['sandbox_reachability'][ $probe ] = is_wp_error( $res ) ? 'error: ' . $res->get_error_message() : (int) wp_remote_retrieve_response_code( $res );
}

echo wp_json_encode( $report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
