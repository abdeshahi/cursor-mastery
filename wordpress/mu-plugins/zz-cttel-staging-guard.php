<?php
/**
 * Plugin Name: CTTEL Staging Guard
 * Description: Staging-only: noindex, disable real payments & customer mail, block outbound webhooks.
 *
 * Active only when the stored site URL (DB, not the request Host) is a staging.* host,
 * independent of CTTEL_STAGING so the guard can never be switched off by a missing constant.
 * Only exception to "no payments": ZarinPal while its own sandbox setting is on.
 */
defined( 'ABSPATH' ) || exit;

if ( ! str_starts_with( strtolower( (string) wp_parse_url( (string) get_option( 'home' ), PHP_URL_HOST ) ), 'staging.' ) ) {
	return;
}

add_filter( 'pre_option_blog_public', static fn() => '0' );
add_action( 'wp_head', static function () {
	echo "<meta name=\"robots\" content=\"noindex, nofollow, noarchive\" />\n";
}, 1 );
add_filter( 'wp_robots', static function ( $robots ) {
	$robots['noindex'] = true;
	$robots['nofollow'] = true;
	$robots['noarchive'] = true;
	return $robots;
} );

/**
 * ZarinPal counts as safe only if the gateway defines a sandbox setting and it is on.
 *
 * @param mixed $gateway
 */
function cttel_staging_guard_zarinpal_is_sandbox( $gateway ): bool {
	if ( ! $gateway instanceof WC_Payment_Gateway ) {
		return false;
	}
	$fields = $gateway->get_form_fields();
	if ( ! isset( $fields['sandbox'] ) ) {
		return false;
	}
	return 'yes' === $gateway->get_option( 'sandbox', 'no' );
}

// Disable all WC payment gateways (no real payments), except ZarinPal in sandbox mode.
add_filter( 'woocommerce_available_payment_gateways', static function ( $gateways ) {
	if ( is_array( $gateways ) && isset( $gateways['WC_ZPal'] ) && cttel_staging_guard_zarinpal_is_sandbox( $gateways['WC_ZPal'] ) ) {
		return array( 'WC_ZPal' => $gateways['WC_ZPal'] );
	}
	return array();
}, 100 );
add_filter( 'pre_option_woocommerce_gateway_order', static fn() => array() );
add_action( 'init', static function () {
	if ( ! class_exists( 'WooCommerce' ) ) {
		return;
	}
	$ids = array( 'bacs', 'cheque', 'cod', 'paypal', 'stripe', 'zarinpal', 'idpay', 'nextpay', 'payir', 'zibal' );
	foreach ( $ids as $id ) {
		update_option( 'woocommerce_' . $id . '_settings', array( 'enabled' => 'no' ) );
	}
}, 20 );

// Do not email customers from staging.
add_filter( 'wp_mail', static function ( $args ) {
	$args['to'] = 'noreply-staging@localhost';
	$args['subject'] = '[STAGING BLOCKED] ' . ( $args['subject'] ?? '' );
	return $args;
}, 1 );
add_filter( 'pre_wp_mail', static function () {
	return true; // short-circuit: pretend sent, do not send
}, 1 );

// Block common outbound webhook / Divar / n8n side effects.
add_filter( 'pre_http_request', static function ( $pre, $args, $url ) {
	$host = wp_parse_url( $url, PHP_URL_HOST );
	if ( ! $host ) {
		return $pre;
	}
	$block = array( 'divar.ir', 'open-api.divar.ir', 'n8n', 'hooks.', 'webhook' );
	foreach ( $block as $needle ) {
		if ( false !== stripos( (string) $host, $needle ) || false !== stripos( (string) $url, $needle ) ) {
			return array(
				'headers'  => array(),
				'body'     => '{"staging":"blocked"}',
				'response' => array( 'code' => 200, 'message' => 'OK' ),
				'cookies'  => array(),
				'filename' => null,
			);
		}
	}
	return $pre;
}, 1, 3 );

add_action( 'admin_notices', static function () {
	echo '<div class="notice notice-warning"><p><strong>CTTEL STAGING</strong> — noindex, payments off (ZarinPal sandbox only), mail/webhooks blocked. Not production.</p></div>';
} );
