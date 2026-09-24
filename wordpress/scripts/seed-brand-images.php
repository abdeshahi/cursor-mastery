<?php
/**
 * Wire Hero image block on homepage after brand assets import.
 *
 * @package CTTEL
 */

$hero_id = isset( $args[0] ) ? (int) $args[0] : 0;
if ( $hero_id <= 0 ) {
	echo "missing hero id\n";
	return;
}

$post_id = 24;
$post    = get_post( $post_id );
if ( ! $post ) {
	echo "homepage missing\n";
	return;
}

$url     = wp_get_attachment_url( $hero_id );
$content = $post->post_content;

$block = sprintf(
	'<!-- wp:image {"id":%1$d,"sizeSlug":"large","linkDestination":"none","className":"cttel-hero__image"} -->'
	. '<figure class="wp-block-image size-large cttel-hero__image">'
	. '<img src="%2$s" alt="CTTEL — موبایل و گجت" class="wp-image-%1$d" loading="lazy" decoding="async"/>'
	. '</figure><!-- /wp:image -->',
	$hero_id,
	esc_url( $url )
);

if ( str_contains( $content, 'cttel-hero__image' ) ) {
	$content = preg_replace(
		'/<!-- wp:image[^>]*cttel-hero__image[^>]*-->.*?<!-- \\/wp:image -->/s',
		$block,
		$content,
		1
	);
} else {
	echo "hero block not found\n";
	return;
}

wp_update_post(
	array(
		'ID'           => $post_id,
		'post_content' => $content,
	)
);

echo "hero_updated\n";
