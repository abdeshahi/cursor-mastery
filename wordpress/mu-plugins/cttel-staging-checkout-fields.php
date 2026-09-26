<?php
/**
 * Staging checkout fields — required mobile, Persian labels (release candidate).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * @param array<string, array<string, mixed>> $fields Billing fields.
 * @return array<string, array<string, mixed>>
 */
function cttel_staging_checkout_billing_phone_field( array $fields ): array {
	if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
		return $fields;
	}
	if ( ! isset( $fields['billing_phone'] ) ) {
		return $fields;
	}
	$fields['billing_phone']['required']     = true;
	$fields['billing_phone']['label']      = __( 'شماره موبایل', 'cttel-store' );
	$fields['billing_phone']['placeholder'] = '09123456789';
	$fields['billing_phone']['priority']   = 90;
	$fields['billing_phone']['class']      = array( 'form-row-wide', 'validate-required', 'validate-phone' );
	return $fields;
}

add_filter( 'woocommerce_billing_fields', 'cttel_staging_checkout_billing_phone_field', 25 );
add_filter(
	'woocommerce_checkout_fields',
	static function ( array $fields ): array {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return $fields;
		}
		if ( isset( $fields['billing']['billing_phone'] ) ) {
			$fields['billing']['billing_phone']['required']     = true;
			$fields['billing']['billing_phone']['label']        = __( 'شماره موبایل', 'cttel-store' );
			$fields['billing']['billing_phone']['placeholder']  = '09123456789';
			$fields['billing']['billing_phone']['class']        = array( 'form-row-wide', 'validate-required', 'validate-phone' );
		}
		return $fields;
	},
	25
);

add_filter(
	'woocommerce_default_address_fields',
	static function ( array $fields ): array {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return $fields;
		}
		if ( isset( $fields['phone'] ) ) {
			$fields['phone']['required'] = true;
			$fields['phone']['label']    = __( 'شماره موبایل', 'cttel-store' );
		}
		return $fields;
	},
	25
);

add_action(
	'woocommerce_after_checkout_validation',
	static function ( $data, $errors ): void {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() ) {
			return;
		}
		if ( ! $errors instanceof WP_Error ) {
			return;
		}
		$phone = is_array( $data ) ? trim( (string) ( $data['billing_phone'] ?? '' ) ) : '';
		if ( '' === $phone ) {
			$errors->add( 'billing_phone', __( 'لطفاً شماره موبایل خود را وارد کنید.', 'cttel-store' ) );
			return;
		}
		$digits = preg_replace( '/\D/', '', $phone );
		if ( is_string( $digits ) && strlen( $digits ) >= 10 && ! preg_match( '/^09\d{9}$/', $digits ) && ! preg_match( '/^9\d{9}$/', $digits ) ) {
			$errors->add( 'billing_phone', __( 'شماره موبایل معتبر نیست. نمونه: 09123456789', 'cttel-store' ) );
		}
	},
	10,
	2
);

add_filter(
	'gettext',
	static function ( $translated, $text, $domain ) {
		if ( ! function_exists( 'cttel_is_staging_site' ) || ! cttel_is_staging_site() || 'woocommerce' !== $domain ) {
			return $translated;
		}
		if ( ! function_exists( 'is_checkout' ) || ! is_checkout() ) {
			return $translated;
		}
		if ( 'Phone' === $text || 'Billing phone' === $text ) {
			return __( 'شماره موبایل', 'cttel-store' );
		}
		if ( 'Free shipping' === $text || 'ارسال رایگان' === $translated ) {
			return cttel_postpaid_shipping_cost_display();
		}
		return $translated;
	},
	998,
	3
);
