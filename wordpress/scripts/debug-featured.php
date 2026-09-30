<?php
$product = wc_get_product( 27 );
if ( ! $product ) {
	echo "no product\n";
	exit( 1 );
}

echo 'featured meta: ' . get_post_meta( 27, '_featured', true ) . "\n";
$terms = wp_get_post_terms( 27, 'product_visibility', array( 'fields' => 'names' ) );
echo 'visibility: ' . implode( ',', (array) $terms ) . "\n";

$q = new WP_Query(
	array(
		'post_type'      => 'product',
		'posts_per_page' => 4,
		'tax_query'      => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_tax_query
			array(
				'taxonomy' => 'product_visibility',
				'field'    => 'name',
				'terms'    => array( 'featured' ),
				'operator' => 'IN',
			),
		),
	)
);
echo 'query count: ' . $q->found_posts . "\n";
