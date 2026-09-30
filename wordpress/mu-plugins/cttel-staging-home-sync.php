<?php
/**
 * Staging-only GitHub sync for homepage mu-plugins (never runs on production).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

if ( ! function_exists( 'cttel_is_staging_site' ) ) {
	function cttel_is_staging_site(): bool {
		if ( defined( 'CTTEL_STAGING' ) && CTTEL_STAGING ) {
			return true;
		}
		$host = isset( $_SERVER['HTTP_HOST'] ) ? strtolower( (string) $_SERVER['HTTP_HOST'] ) : '';
		return str_contains( $host, 'staging.' ) || str_contains( $host, 'staging.cttel' );
	}
}

if ( ! function_exists( 'cttel_staging_sync_homepage_mu_from_github' ) ) {
	function cttel_staging_sync_homepage_mu_from_github(): void {
		if ( ! cttel_is_staging_site() || ! function_exists( 'wp_remote_get' ) ) {
			return;
		}
		if ( get_transient( 'cttel_staging_home_mu_sync' ) ) {
			return;
		}
		set_transient( 'cttel_staging_home_mu_sync', 1, 5 * MINUTE_IN_SECONDS );

		$branch = 'cursor/cttel-homepage-rebuild-72ff';
		$base   = 'https://raw.githubusercontent.com/abdeshahi/cursor-mastery/' . $branch . '/wordpress/mu-plugins/';
		$files  = array(
			'cttel-staging-home-sync.php',
			'cttel-homepage.php',
			'cttel-homepage-render.php',
			'cttel-homepage.css',
			'cttel-home-mockup.css',
		);

		foreach ( $files as $file ) {
			$response = wp_remote_get(
				$base . $file,
				array(
					'timeout' => 20,
				)
			);
			if ( is_wp_error( $response ) || 200 !== (int) wp_remote_retrieve_response_code( $response ) ) {
				continue;
			}
			$body = wp_remote_retrieve_body( $response );
			if ( '' === $body ) {
				continue;
			}
			$dest = WPMU_PLUGIN_DIR . '/' . $file;
			if ( is_writable( $dest ) ) {
				// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_file_put_contents
				file_put_contents( $dest, $body );
			}
		}
	}

	add_action( 'muplugins_loaded', 'cttel_staging_sync_homepage_mu_from_github', 0 );
}
