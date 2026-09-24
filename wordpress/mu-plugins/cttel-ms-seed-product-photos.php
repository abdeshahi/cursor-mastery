<?php
/**
 * WP-CLI: seed featured images from local cttel-ms product photos (staging only).
 *
 *   docker exec wp_staging_app wp eval-file wp-content/mu-plugins/cttel-ms-seed-product-photos.php --allow-root
 *
 * Skips products that already have a featured image or gallery. Admin changes always win afterward.
 *
 * @package CTTEL
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit( 1 );
}

if ( ! class_exists( 'WP_CLI' ) ) {
	return;
}

if ( ! function_exists( 'wc_get_product' ) || ! function_exists( 'cttel_ms_product_local_photo_relative_path' ) ) {
	WP_CLI::error( 'WooCommerce and cttel-mobile-storefront-assets must be loaded.' );
}

/**
 * @return int Attachment ID or 0.
 */
function cttel_ms_seed_attachment_from_file( string $file, int $parent_id, string $title ): int {
	$filename = basename( $file );
	$upload   = wp_upload_bits( $filename, null, (string) file_get_contents( $file ) );
	if ( ! empty( $upload['error'] ) ) {
		WP_CLI::warning( $upload['error'] );
		return 0;
	}
	require_once ABSPATH . 'wp-admin/includes/image.php';
	$filetype = wp_check_filetype( $filename, null );
	$attachment = array(
		'post_mime_type' => $filetype['type'],
		'post_title'     => sanitize_text_field( $title ),
		'post_content'   => '',
		'post_status'    => 'inherit',
		'post_parent'    => $parent_id,
	);
	$attach_id = wp_insert_attachment( $attachment, $upload['file'], $parent_id );
	if ( is_wp_error( $attach_id ) ) {
		WP_CLI::warning( $attach_id->get_error_message() );
		return 0;
	}
	$meta = wp_generate_attachment_metadata( $attach_id, $upload['file'] );
	wp_update_attachment_metadata( $attach_id, $meta );
	return (int) $attach_id;
}

$assets_dir = WP_CONTENT_DIR . '/mu-plugins/assets/cttel-ms';
if ( ! is_dir( $assets_dir ) ) {
	WP_CLI::error( 'Missing mu-plugins/assets/cttel-ms on this site.' );
}

require_once ABSPATH . 'wp-admin/includes/file.php';

$products = wc_get_products(
	array(
		'limit'  => -1,
		'status' => 'publish',
		'return' => 'objects',
	)
);

$imported = 0;
$skipped  = 0;

foreach ( $products as $product ) {
	if ( ! $product instanceof WC_Product ) {
		continue;
	}
	if ( $product->get_image_id() > 0 ) {
		++$skipped;
		continue;
	}
	if ( ! empty( $product->get_gallery_image_ids() ) ) {
		++$skipped;
		continue;
	}
	$rel = cttel_ms_product_local_photo_relative_path( $product );
	if ( '' === $rel || ! is_readable( $assets_dir . '/' . ltrim( $rel, '/' ) ) ) {
		continue;
	}
	$file      = $assets_dir . '/' . ltrim( $rel, '/' );
	$attach_id = cttel_ms_seed_attachment_from_file( $file, $product->get_id(), $product->get_name() );
	if ( $attach_id > 0 ) {
		$product->set_image_id( $attach_id );
		$product->save();
		++$imported;
		WP_CLI::log( sprintf( 'Set featured image for #%d %s', $product->get_id(), $product->get_name() ) );
	}
}

WP_CLI::success( sprintf( 'Imported %d featured images; skipped %d products that already had media.', $imported, $skipped ) );
