<?php
/**
 * CTTEL store helpers — registers Toman (IRT) for WooCommerce admin.
 *
 * Does NOT force currency or appearance. Shop manager chooses currency in:
 * WooCommerce → Settings → General → Currency options.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Add Toman to the currency dropdown in WooCommerce settings. */
add_filter(
	'woocommerce_currencies',
	static function ( $currencies ) {
		$currencies['IRT'] = __( 'تومان (ایران)', 'cttel-store' );
		return $currencies;
	}
);

/** Display symbol when IRT is selected in WooCommerce settings. */
add_filter(
	'woocommerce_currency_symbol',
	static function ( $symbol, $currency ) {
		if ( 'IRT' === $currency ) {
			return 'تومان';
		}
		return $symbol;
	},
	10,
	2
);
