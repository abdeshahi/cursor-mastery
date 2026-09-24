<?php
/**
 * WooCommerce staging audit — run: wp eval-file staging-wc-audit.php --allow-root
 *
 * @package CTTEL
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit( "Run inside WordPress.\n" );
}

require_once dirname( __DIR__ ) . '/mu-plugins/cttel-staging-wc-readiness.php';

$snap = cttel_staging_wc_audit_snapshot();
echo wp_json_encode( $snap, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE ) . "\n";
