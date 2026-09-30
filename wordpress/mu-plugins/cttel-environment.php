<?php
/**
 * CTTEL environment detection — single source of truth for staging-only behavior.
 *
 * Staging is opt-in via wp-config.php of the staging install only:
 *   define( 'CTTEL_STAGING', true );
 *
 * The request Host header is never trusted. As a second guard, the site URL stored
 * in the database must also be a staging host, so a copied wp-config.php cannot
 * switch production into staging mode.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'cttel_is_staging_site' ) ) {
	function cttel_is_staging_site(): bool {
		static $is_staging = null;
		if ( null !== $is_staging ) {
			return $is_staging;
		}
		if ( ! defined( 'CTTEL_STAGING' ) || true !== CTTEL_STAGING ) {
			$is_staging = false;
			return $is_staging;
		}
		$host       = strtolower( (string) wp_parse_url( (string) get_option( 'home' ), PHP_URL_HOST ) );
		$is_staging = str_starts_with( $host, 'staging.' );
		return $is_staging;
	}
}

if ( ! function_exists( 'cttel_staging_audit_request_allowed' ) ) {
	/**
	 * Staging JSON audit endpoints: shop managers, or QA scripts sending
	 * X-CTTEL-Audit-Token matching CTTEL_STAGING_AUDIT_TOKEN (wp-config, >= 32 chars).
	 */
	function cttel_staging_audit_request_allowed(): bool {
		if ( ! cttel_is_staging_site() ) {
			return false;
		}
		if ( function_exists( 'current_user_can' ) && current_user_can( 'manage_woocommerce' ) ) {
			return true;
		}
		if ( ! defined( 'CTTEL_STAGING_AUDIT_TOKEN' ) ) {
			return false;
		}
		$expected = (string) CTTEL_STAGING_AUDIT_TOKEN;
		if ( strlen( $expected ) < 32 ) {
			return false;
		}
		$given = isset( $_SERVER['HTTP_X_CTTEL_AUDIT_TOKEN'] ) ? (string) wp_unslash( $_SERVER['HTTP_X_CTTEL_AUDIT_TOKEN'] ) : ''; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized
		return '' !== $given && hash_equals( $expected, $given );
	}
}
