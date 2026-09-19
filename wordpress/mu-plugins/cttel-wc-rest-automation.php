<?php
/**
 * Expose CTTEL product meta for WooCommerce REST automation (n8n).
 * No storefront or UI changes.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Installment meta used by cttel-product-cards.php */
const CTTEL_WC_REST_INSTALLMENT_META = '_cttel_installment_available';

add_action(
	'init',
	static function (): void {
		register_post_meta(
			'product',
			CTTEL_WC_REST_INSTALLMENT_META,
			array(
				'type'              => 'string',
				'single'            => true,
				'show_in_rest'      => true,
				'auth_callback'     => static function (): bool {
					return current_user_can( 'edit_products' );
				},
				'sanitize_callback' => static function ( $value ) {
					return 'yes' === $value ? 'yes' : 'no';
				},
			)
		);
	},
	20
);

/**
 * Allow WooCommerce REST consumers with edit_products capability via API keys.
 * Values: yes | no
 */
add_filter(
	'woocommerce_rest_prepare_product_object',
	static function ( $response, $product, $request ) {
		if ( ! $response instanceof WP_REST_Response ) {
			return $response;
		}
		$data = $response->get_data();
		if ( ! isset( $data['meta_data'] ) || ! is_array( $data['meta_data'] ) ) {
			return $response;
		}
		$has = false;
		foreach ( $data['meta_data'] as $row ) {
			if ( isset( $row['key'] ) && CTTEL_WC_REST_INSTALLMENT_META === $row['key'] ) {
				$has = true;
				break;
			}
		}
		if ( ! $has ) {
			$data['meta_data'][] = array(
				'id'    => 0,
				'key'   => CTTEL_WC_REST_INSTALLMENT_META,
				'value' => $product->get_meta( CTTEL_WC_REST_INSTALLMENT_META, true ) ?: 'no',
			);
			$response->set_data( $data );
		}
		return $response;
	},
	10,
	3
);
