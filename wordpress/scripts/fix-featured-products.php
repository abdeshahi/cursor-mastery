<?php
/**
 * One-off: sync featured flag to product_visibility taxonomy.
 *
 * @package CTTEL
 */

$ids = array( 27, 28, 29, 30 );

foreach ( $ids as $id ) {
	update_post_meta( $id, '_featured', 'yes' );
	$product = wc_get_product( $id );
	if ( ! $product ) {
		continue;
	}
	wp_set_post_terms( $id, array( 'featured' ), 'product_visibility', true );
}

$featured = wc_get_products(
	array(
		'limit'    => 4,
		'featured' => true,
		'return'   => 'ids',
	)
);

echo 'featured_ids=' . implode( ',', $featured ) . PHP_EOL;
