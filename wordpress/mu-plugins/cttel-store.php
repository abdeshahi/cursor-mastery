<?php
/**
 * CTTEL store helpers — currency display only (no layout/CSS hard-coding).
 *
 * Prices are entered in Toman in wp-admin. WooCommerce math stays unchanged.
 * Iranian payment gateways can multiply by 10 to Rial at checkout when integrated.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * Use custom Toman currency code (IRT) with Persian symbol.
 */
add_filter(
	'woocommerce_currencies',
	static function ( $currencies ) {
		$currencies['IRT'] = 'تومان (ایران)';
		return $currencies;
	}
);

add_filter(
	'woocommerce_currency',
	static function () {
		return 'IRT';
	}
);

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

add_filter(
	'woocommerce_price_format',
	static function () {
		return '%2$s %1$s';
	}
);
