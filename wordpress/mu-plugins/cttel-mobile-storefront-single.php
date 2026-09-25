<?php
/**
 * Single product page — mobile storefront.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

function cttel_ms_is_single_product(): bool {
	return function_exists( 'is_product' ) && is_product();
}

function cttel_ms_installment_url(): string {
	if ( function_exists( 'cttel_installment_default_url' ) ) {
		return cttel_installment_default_url();
	}
	$page = get_page_by_path( 'installment' );
	if ( $page instanceof WP_Post ) {
		return get_permalink( $page );
	}
	return home_url( '/installment/' );
}

/**
 * Compact WooCommerce attributes / short description (no invented data).
 */
function cttel_ms_render_product_information_block( WC_Product $product ): void {
	if ( function_exists( 'cttel_product_is_used' ) && cttel_product_is_used( $product ) ) {
		return;
	}
	$rows_html = '';
	if ( function_exists( 'wc_display_product_attributes' ) ) {
		ob_start();
		wc_display_product_attributes( $product );
		$table = (string) ob_get_clean();
		if ( '' !== trim( wp_strip_all_tags( $table ) ) ) {
			$rows_html = $table;
		}
	}
	$short = trim( (string) $product->get_short_description() );
	if ( '' === $rows_html && '' === $short ) {
		return;
	}
	echo '<section class="cttel-ms-product-info" aria-labelledby="cttel-ms-product-info-title">';
	echo '<h2 id="cttel-ms-product-info-title" class="cttel-ms-product-info__title">' . esc_html__( 'مشخصات و توضیحات', 'cttel-store' ) . '</h2>';
	if ( '' !== $short ) {
		echo '<div class="cttel-ms-product-info__desc">' . wp_kses_post( wpautop( $short ) ) . '</div>';
	}
	if ( '' !== $rows_html ) {
		echo '<div class="cttel-ms-product-info__attrs">' . $rows_html . '</div>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	}
	echo '</section>';
}

function cttel_ms_render_pdp_shipping_block(): void {
	?>
	<section class="cttel-ms-pdp-shipping" aria-labelledby="cttel-ms-pdp-shipping-title">
		<h2 id="cttel-ms-pdp-shipping-title" class="cttel-ms-pdp-shipping__title"><?php esc_html_e( 'ارسال', 'cttel-store' ); ?></h2>
		<p class="cttel-ms-pdp-shipping__line"><?php esc_html_e( 'ارسال با تیپاکس یا ماهکس', 'cttel-store' ); ?></p>
		<p class="cttel-ms-pdp-shipping__line cttel-ms-pdp-shipping__line--muted"><?php esc_html_e( 'هزینه ارسال هنگام تحویل توسط مشتری به شرکت حمل پرداخت می‌شود.', 'cttel-store' ); ?></p>
		<p class="cttel-ms-pdp-shipping__note"><?php esc_html_e( 'مبلغ کالا در همین صفحه به‌صورت آنلاین پرداخت می‌شود؛ هزینه حمل جداگانه و هنگام تحویل به پیک/شرکت حمل است.', 'cttel-store' ); ?></p>
	</section>
	<?php
}

function cttel_ms_render_pdp_trust_block(): void {
	$items = array(
		__( 'پرداخت امن آنلاین مبلغ کالا', 'cttel-store' ),
		__( 'ضمانت اصالت کالا', 'cttel-store' ),
		__( 'پشتیبانی فروشگاه CTTEL', 'cttel-store' ),
	);
	?>
	<section class="cttel-ms-pdp-trust" aria-label="<?php esc_attr_e( 'اطمینان خرید', 'cttel-store' ); ?>">
		<ul class="cttel-ms-pdp-trust__list">
			<?php foreach ( $items as $item ) : ?>
				<li><?php echo esc_html( $item ); ?></li>
			<?php endforeach; ?>
		</ul>
	</section>
	<?php
}

function cttel_ms_render_pdp_installment_block(): void {
	$url = cttel_ms_installment_url();
	?>
	<section class="cttel-ms-pdp-installment" aria-labelledby="cttel-ms-pdp-installment-title">
		<h2 id="cttel-ms-pdp-installment-title" class="screen-reader-text"><?php esc_html_e( 'خرید اقساطی', 'cttel-store' ); ?></h2>
		<p class="cttel-ms-pdp-installment__text"><?php esc_html_e( 'خرید اقساطی به‌صورت حضوری و پس از بررسی شرایط انجام می‌شود.', 'cttel-store' ); ?></p>
		<a class="cttel-ms-btn cttel-ms-btn--outline cttel-ms-pdp-installment__cta" href="<?php echo esc_url( $url ); ?>"><?php esc_html_e( 'مشاهده شرایط خرید اقساطی', 'cttel-store' ); ?></a>
	</section>
	<?php
}

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_ms_is_single_product() && cttel_mobile_storefront_uses_shell() ) {
			$classes[] = 'cttel-ms-single';
			global $product;
			if ( $product instanceof WC_Product && $product->get_review_count() > 0 ) {
				$classes[] = 'cttel-ms-pdp-has-reviews';
			}
		}
		return $classes;
	}
);

add_filter(
	'comments_template',
	static function ( string $template ): string {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return $template;
		}
		$custom = __DIR__ . '/templates/cttel-ms-single-product-reviews.php';
		return is_readable( $custom ) ? $custom : $template;
	},
	20
);

add_action(
	'woocommerce_before_main_content',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		$back = wp_get_referer();
		if ( ! $back || false !== strpos( $back, 'add-to-cart' ) ) {
			$terms = get_the_terms( $product->get_id(), 'product_cat' );
			if ( is_array( $terms ) && ! empty( $terms ) && $terms[0] instanceof WP_Term ) {
				$back = get_term_link( $terms[0] );
			} else {
				$back = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
			}
		}
		?>
		<main class="cttel-ms-main cttel-ms-main--single" id="cttel-ms-single-main">
			<div class="cttel-ms-single-head">
				<a class="cttel-ms-single-head__back" href="<?php echo esc_url( is_string( $back ) ? $back : home_url( '/' ) ); ?>">
					<?php echo cttel_mobile_storefront_icon( 'chev', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<span><?php esc_html_e( 'بازگشت', 'cttel-store' ); ?></span>
				</a>
				<a class="cttel-ms-single-head__cart" href="<?php echo esc_url( cttel_mobile_storefront_cart_url() ); ?>" aria-label="<?php esc_attr_e( 'سبد خرید', 'cttel-store' ); ?>">
					<?php echo cttel_mobile_storefront_icon( 'cart', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				</a>
			</div>
		<?php
	},
	5
);

add_action(
	'woocommerce_after_main_content',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		echo '</main>';
	},
	50
);

add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		if ( function_exists( 'cttel_product_is_used' ) && cttel_product_is_used( $product ) ) {
			echo '<p class="cttel-ms-single__badge cttel-ms-single__badge--used">' . esc_html__( 'کارکرده', 'cttel-store' ) . '</p>';
		} elseif ( function_exists( 'cttel_product_is_new' ) && cttel_product_is_new( $product ) ) {
			echo '<p class="cttel-ms-single__badge cttel-ms-single__badge--new">' . esc_html__( 'نو', 'cttel-store' ) . '</p>';
		}
		if ( function_exists( 'cttel_product_stock_label' ) ) {
			printf(
				'<p class="cttel-ms-single__stock %1$s">%2$s</p>',
				esc_attr( cttel_product_stock_class( $product ) ),
				esc_html( cttel_product_stock_label( $product ) )
			);
		}
	},
	6
);

add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		cttel_ms_render_product_information_block( $product );
	},
	32
);

add_action(
	'woocommerce_single_product_summary',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		cttel_ms_render_pdp_shipping_block();
		cttel_ms_render_pdp_trust_block();
		cttel_ms_render_pdp_installment_block();
	},
	36
);

add_action(
	'wp',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_meta', 40 );
		remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_excerpt', 20 );
		remove_action( 'woocommerce_after_single_product_summary', 'woocommerce_output_product_data_tabs', 10 );
		remove_action( 'woocommerce_after_single_product_summary', 'comments_template', 50 );
		add_action( 'woocommerce_after_single_product_summary', 'woocommerce_output_product_data_tabs', 28 );
		add_action( 'woocommerce_after_single_product_summary', 'comments_template', 42 );
	},
	20
);

add_filter(
	'woocommerce_product_tabs',
	static function ( array $tabs ): array {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return $tabs;
		}
		unset( $tabs['additional_information'], $tabs['reviews'] );
		if ( isset( $tabs['description'] ) ) {
			global $product;
			if ( $product instanceof WC_Product && '' === trim( (string) $product->get_description() ) ) {
				unset( $tabs['description'] );
			}
		}
		return $tabs;
	},
	50
);

add_filter(
	'woocommerce_output_related_products_args',
	static function ( array $args ): array {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return $args;
		}
		$args['posts_per_page'] = 4;
		$args['columns']        = 2;
		return $args;
	}
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! cttel_ms_is_single_product() || ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		wp_dequeue_style( 'cttel-storefront' );
		if ( function_exists( 'WC' ) ) {
			wp_enqueue_script( 'wc-single-product' );
		}
		wp_register_script( 'cttel-ms-single-reviews', false, array( 'jquery' ), CTTEL_MOBILE_STOREFRONT_VERSION, true );
		wp_enqueue_script( 'cttel-ms-single-reviews' );
		wp_add_inline_script(
			'cttel-ms-single-reviews',
			"(function () {
	function bindReviews(root) {
		if (!root || root.dataset.cttelReviewsBound) return;
		root.dataset.cttelReviewsBound = '1';
		var toggle = root.querySelector('.cttel-ms-reviews-toggle');
		var formWrap = root.querySelector('#review_form_wrapper');
		if (!toggle || !formWrap) return;
		formWrap.hidden = true;
		root.classList.remove('is-review-form-open');
		toggle.addEventListener('click', function () {
			var open = formWrap.hidden;
			formWrap.hidden = !open;
			root.classList.toggle('is-review-form-open', open);
			toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
			if (open) formWrap.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
		});
	}
	function initReviews() {
		document.querySelectorAll('#reviews').forEach(function (node, index) {
			if (index > 0) {
				node.setAttribute('hidden', 'hidden');
				node.setAttribute('aria-hidden', 'true');
				return;
			}
			bindReviews(node);
		});
		document.querySelectorAll('.woocommerce-Tabs-panel--reviews').forEach(function (panel) {
			panel.setAttribute('hidden', 'hidden');
		});
	}
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', initReviews);
	} else {
		initReviews();
	}
})();"
		);
	},
	125
);
