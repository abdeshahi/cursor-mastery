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
		$commenter    = wp_get_current_commenter();
		$comment_form = array(
			'title_reply'         => have_comments()
				? esc_html__( 'Add a review', 'woocommerce' )
				: sprintf( esc_html__( 'Be the first to review &ldquo;%s&rdquo;', 'woocommerce' ), get_the_title() ),
			'title_reply_to'      => esc_html__( 'Leave a Reply to %s', 'woocommerce' ),
			'title_reply_before'  => '<span id="reply-title" class="comment-reply-title" role="heading" aria-level="3">',
			'title_reply_after'   => '</span>',
			'comment_notes_after' => '',
			'label_submit'        => esc_html__( 'Submit', 'woocommerce' ),
			'logged_in_as'        => '',
			'comment_field'       => '',
		);

		$name_email_required = (bool) get_option( 'require_name_email', 1 );
		$fields              = array(
			'author' => array(
				'label'        => __( 'Name', 'woocommerce' ),
				'type'         => 'text',
				'value'        => $commenter['comment_author'],
				'required'     => $name_email_required,
				'autocomplete' => 'name',
			),
			'email'  => array(
				'label'        => __( 'Email', 'woocommerce' ),
				'type'         => 'email',
				'value'        => $commenter['comment_author_email'],
				'required'     => $name_email_required,
				'autocomplete' => 'email',
			),
		);

		$comment_form['fields'] = array();

		foreach ( $fields as $key => $field ) {
			$field_html  = '<p class="comment-form-' . esc_attr( $key ) . '">';
			$field_html .= '<label for="' . esc_attr( $key ) . '">' . esc_html( $field['label'] );

			if ( $field['required'] ) {
				$field_html .= '&nbsp;<span class="required">*</span>';
			}

			$field_html .= '</label><input id="' . esc_attr( $key ) . '" name="' . esc_attr( $key ) . '" type="' . esc_attr( $field['type'] ) . '" autocomplete="' . esc_attr( $field['autocomplete'] ) . '" value="' . esc_attr( $field['value'] ) . '" size="30" ' . ( $field['required'] ? 'required' : '' ) . ' /></p>';

			$comment_form['fields'][ $key ] = $field_html;
		}

		$account_page_url = wc_get_page_permalink( 'myaccount' );
		if ( $account_page_url ) {
			$comment_form['must_log_in'] = '<p class="must-log-in">' . sprintf(
				/* translators: %1$s opening anchor, %2$s closing anchor */
				esc_html__( 'You must be %1$slogged in%2$s to post a review.', 'woocommerce' ),
				'<a href="' . esc_url( $account_page_url ) . '">',
				'</a>'
			) . '</p>';
		}

		if ( wc_review_ratings_enabled() ) {
			$comment_form['comment_field'] = '<div class="comment-form-rating"><label for="rating" id="comment-form-rating-label">' . esc_html__( 'Your rating', 'woocommerce' ) . ( wc_review_ratings_required() ? '&nbsp;<span class="required">*</span>' : '' ) . '</label><select name="rating" id="rating" required>
						<option value="">' . esc_html__( 'Rate&hellip;', 'woocommerce' ) . '</option>
						<option value="5">' . esc_html__( 'Perfect', 'woocommerce' ) . '</option>
						<option value="4">' . esc_html__( 'Good', 'woocommerce' ) . '</option>
						<option value="3">' . esc_html__( 'Average', 'woocommerce' ) . '</option>
						<option value="2">' . esc_html__( 'Not that bad', 'woocommerce' ) . '</option>
						<option value="1">' . esc_html__( 'Very poor', 'woocommerce' ) . '</option>
					</select></div>';
		}

		$comment_form['comment_field'] .= '<p class="comment-form-comment"><label for="comment">' . esc_html__( 'Your review', 'woocommerce' ) . '&nbsp;<span class="required">*</span></label><textarea id="comment" name="comment" cols="45" rows="8" required></textarea></p>';

		?>
		<div id="review_form_wrapper" class="cttel-ms-reviews-form-wrap" hidden>
			<div id="review_form">
				<?php
				comment_form( apply_filters( 'woocommerce_product_review_comment_form_args', $comment_form ), $product->get_id() );
				?>
			</div>
		</div>
	<?php else : ?>
		<p class="woocommerce-verification-required"><?php esc_html_e( 'فقط مشتریانی که این محصول را خریده‌اند می‌توانند نظر ثبت کنند.', 'woocommerce' ); ?></p>
	<?php endif; ?>
</div>
