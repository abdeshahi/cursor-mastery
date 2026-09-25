<?php
/**
 * Mobile storefront — single product reviews (one section, collapsed form by default).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

global $product;

if ( ! $product instanceof WC_Product || ! comments_open() ) {
	return;
}

$count = (int) $product->get_review_count();
?>
<div id="reviews" class="woocommerce-Reviews cttel-ms-reviews-root">
	<div class="cttel-ms-reviews-head">
		<h2 class="cttel-ms-reviews-head__title">
			<?php
			printf(
				/* translators: %d: review count */
				esc_html__( 'نظرات کاربران (%d)', 'cttel-store' ),
				$count
			);
			?>
		</h2>
		<?php if ( 0 === $count ) : ?>
			<p class="cttel-ms-reviews-head__empty"><?php esc_html_e( 'هنوز نظری برای این محصول ثبت نشده است.', 'cttel-store' ); ?></p>
		<?php endif; ?>
		<button type="button" class="cttel-ms-btn cttel-ms-btn--outline cttel-ms-reviews-toggle" aria-expanded="false" aria-controls="review_form_wrapper">
			<?php esc_html_e( 'ثبت نظر', 'cttel-store' ); ?>
		</button>
	</div>

	<?php if ( have_comments() ) : ?>
		<div id="comments">
			<ol class="commentlist">
				<?php
				wp_list_comments(
					apply_filters(
						'woocommerce_product_review_list_args',
						array(
							'callback' => 'woocommerce_comments',
						)
					)
				);
				?>
			</ol>
			<?php
			if ( get_comment_pages_count() > 1 && get_option( 'page_comments' ) ) :
				echo '<nav class="woocommerce-pagination">';
				paginate_comments_links(
					apply_filters(
						'woocommerce_comment_pagination_args',
						array(
							'prev_text' => is_rtl() ? '&rarr;' : '&larr;',
							'next_text' => is_rtl() ? '&larr;' : '&rarr;',
							'type'      => 'list',
						)
					)
				);
				echo '</nav>';
			endif;
			?>
		</div>
	<?php endif; ?>

	<?php
	$verified = get_option( 'woocommerce_review_rating_verification_required' ) === 'no'
		|| wc_customer_bought_product( '', get_current_user_id(), $product->get_id() );
	if ( $verified ) :
		$comment_form = array(
			'title_reply'         => have_comments()
				? esc_html__( 'Add a review', 'woocommerce' )
				: sprintf( esc_html__( 'Be the first to review &ldquo;%s&rdquo;', 'woocommerce' ), get_the_title() ),
			'title_reply_to'      => esc_html__( 'Leave a Reply', 'woocommerce' ),
			'title_reply_before'  => '<span id="reply-title" class="comment-reply-title screen-reader-text">',
			'title_reply_after'   => '</span>',
			'comment_notes_after' => '',
			'label_submit'        => esc_html__( 'Submit', 'woocommerce' ),
			'logged_in_as'        => '',
			'comment_field'       => '',
		);
		?>
		<div id="review_form_wrapper" class="cttel-ms-reviews-form-wrap" hidden>
			<div id="review_form">
				<?php comment_form( apply_filters( 'woocommerce_product_review_comment_form_args', $comment_form ) ); ?>
			</div>
		</div>
	<?php else : ?>
		<p class="woocommerce-verification-required"><?php esc_html_e( 'فقط مشتریانی که این محصول را خریده‌اند می‌توانند نظر ثبت کنند.', 'woocommerce' ); ?></p>
	<?php endif; ?>
</div>
