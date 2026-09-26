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

if ( function_exists( 'WC' ) && WC()->api_request_url ) {
	$base = WC()->api_request_url( 'WC_ZPal' );
	$report['gateway']['callback_base_url'] = $base;
	$report['gateway']['callback_example']  = add_query_arg( 'wc_order', 'ORDER_ID', $base );
}

echo wp_json_encode( $report, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
