<?php
/**
 * CTTEL product cards — minimal styling, installment badge, block grid markup.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Product meta key for installment availability. */
const CTTEL_INSTALLMENT_META = '_cttel_installment_available';

/** Whether product supports installment (admin checkbox on product edit). */
function cttel_product_has_installment( WC_Product $product ): bool {
	return 'yes' === $product->get_meta( CTTEL_INSTALLMENT_META, true );
}

/** Human-readable stock label. */
function cttel_product_stock_label( WC_Product $product ): string {
	if ( ! $product->managing_stock() && $product->is_in_stock() ) {
		return __( 'موجود', 'cttel-store' );
	}

	if ( $product->is_on_backorder() ) {
		return __( 'پیش‌سفارش', 'cttel-store' );
	}

	if ( ! $product->is_in_stock() ) {
		return __( 'ناموجود', 'cttel-store' );
	}

	$qty = $product->get_stock_quantity();
	if ( null !== $qty && $qty > 0 && $qty <= 5 ) {
		/* translators: %d: stock quantity */
		return sprintf( __( 'تنها %d عدد', 'cttel-store' ), $qty );
	}

	return __( 'موجود', 'cttel-store' );
}

/** Stock status CSS modifier. */
function cttel_product_stock_class( WC_Product $product ): string {
	if ( ! $product->is_in_stock() ) {
		return 'is-out-of-stock';
	}
	if ( $product->is_on_backorder() ) {
		return 'is-on-backorder';
	}
	return 'is-in-stock';
}

/** Build badge row HTML. */
function cttel_product_card_badges( WC_Product $product, string $wc_badge = '' ): string {
	$html = '';

	if ( $product->is_on_sale() ) {
		$html .= '<span class="cttel-pcard-badge cttel-pcard-badge--sale">' . esc_html__( 'حراج', 'cttel-store' ) . '</span>';
	} elseif ( $wc_badge ) {
		$html .= wp_kses_post( $wc_badge );
	}

	if ( cttel_product_has_installment( $product ) ) {
		$html .= '<span class="cttel-pcard-badge cttel-pcard-badge--installment">' . esc_html__( 'اقساطی', 'cttel-store' ) . '</span>';
	}

	if ( '' === $html ) {
		return '';
	}

	return '<div class="cttel-pcard-badges">' . $html . '</div>';
}

/**
 * Read property from WooCommerce block product data (object or array).
 *
 * @param object|array $data Block product data.
 */
function cttel_block_product_data( $data, string $key ) {
	if ( is_object( $data ) && isset( $data->{$key} ) ) {
		return $data->{$key};
	}
	if ( is_array( $data ) && isset( $data[ $key ] ) ) {
		return $data[ $key ];
	}
	return null;
}

/** Professional product card for WooCommerce block grids. */
function cttel_block_product_card_html( string $html, $data, WC_Product $product ): string {
	$permalink = esc_url( cttel_block_product_data( $data, 'permalink' ) ?: $product->get_permalink() );
	$image     = cttel_block_product_data( $data, 'image' ) ?: $product->get_image(
		'woocommerce_thumbnail',
		array(
			'class'   => 'cttel-pcard__img',
			'loading' => 'lazy',
		)
	);
	$price     = cttel_block_product_data( $data, 'price' ) ?: $product->get_price_html();
	$button    = cttel_block_product_data( $data, 'button' ) ?: sprintf(
		'<a href="%s" class="button cttel-pcard__btn wp-element-button">%s</a>',
		esc_url( $permalink ),
		esc_html__( 'مشاهده محصول', 'cttel-store' )
	);
	$badges    = cttel_product_card_badges( $product, (string) ( cttel_block_product_data( $data, 'badge' ) ?: '' ) );
	$stock     = esc_html( cttel_product_stock_label( $product ) );
	$stock_cls = esc_attr( cttel_product_stock_class( $product ) );

	return sprintf(
		'<li class="wc-block-grid__product cttel-pcard">
			<a href="%1$s" class="cttel-pcard__link wc-block-grid__product-link">
				<div class="cttel-pcard__media">%2$s%3$s</div>
				<h3 class="wc-block-grid__product-title cttel-pcard__title">%4$s</h3>
			</a>
			<div class="cttel-pcard__meta">
				<div class="cttel-pcard__price">%5$s</div>
				<p class="cttel-pcard__stock %6$s">%7$s</p>
			</div>
			<div class="cttel-pcard__actions">%8$s</div>
		</li>',
		$permalink,
		$badges,
		$image,
		esc_html( $product->get_name() ),
		$price,
		$stock_cls,
		$stock,
		$button
	);
}

add_filter( 'woocommerce_blocks_product_grid_item_html', 'cttel_block_product_card_html', 10, 3 );

/** Classic loop badges (shortcode / archive). */
add_action(
	'woocommerce_before_shop_loop_item_title',
	static function (): void {
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		echo '<div class="cttel-pcard__media">';
		echo cttel_product_card_badges( $product ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	},
	4
);

add_action(
	'woocommerce_before_shop_loop_item_title',
	static function (): void {
		echo '</div>';
	},
	12
);

add_action(
	'woocommerce_after_shop_loop_item_title',
	static function (): void {
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		printf(
			'<p class="cttel-pcard__stock %1$s">%2$s</p>',
			esc_attr( cttel_product_stock_class( $product ) ),
			esc_html( cttel_product_stock_label( $product ) )
		);
	},
	8
);

/** Installment checkbox on product edit screen. */
add_action(
	'woocommerce_product_options_general_product_data',
	static function (): void {
		woocommerce_wp_checkbox(
			array(
				'id'          => CTTEL_INSTALLMENT_META,
				'label'       => __( 'امکان خرید اقساطی', 'cttel-store' ),
				'description' => __( 'در صورت فعال بودن، برچسب «اقساطی» روی کارت محصول نمایش داده می‌شود.', 'cttel-store' ),
				'desc_tip'    => true,
			)
		);
	}
);

add_action(
	'woocommerce_process_product_meta',
	static function ( int $post_id ): void {
		$value = isset( $_POST[ CTTEL_INSTALLMENT_META ] ) ? 'yes' : 'no'; // phpcs:ignore WordPress.Security.NonceVerification.Missing
		update_post_meta( $post_id, CTTEL_INSTALLMENT_META, $value );
	}
);

/** Use CTTEL brand placeholder for products without a featured image. */
add_filter(
	'woocommerce_placeholder_img',
	static function ( $html, $size, $dimensions ) {
		$attach_id = absint( get_option( 'cttel_product_placeholder_id', 0 ) );
		if ( $attach_id <= 0 ) {
			return $html;
		}
		$img = wp_get_attachment_image(
			$attach_id,
			$size,
			false,
			array(
				'class'   => 'cttel-pcard__img woocommerce-placeholder wp-post-image',
				'loading' => 'lazy',
				'alt'     => '',
			)
		);
		return $img ?: $html;
	},
	10,
	3
);

/** Premium product card + grid CSS (design tokens from cttel-design-system). */
function cttel_storefront_inline_css(): string {
	return 'html,body{overflow-x:hidden;}'
		. '.cttel-products .wc-block-grid__products,.cttel-products ul.products{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(.65rem,1.5vw,1rem);list-style:none;margin:0;padding:0;}'
		. '.cttel-products .wc-block-grid__product,.cttel-products ul.products li.product{margin:0!important;width:100%!important;float:none!important;}'
		. '.cttel-pcard{display:flex;flex-direction:column;height:100%;min-width:0;background:var(--cttel-surface,#fff);border:1px solid var(--cttel-border,rgba(20,28,38,.1));border-radius:var(--cttel-radius-lg,16px);padding:0;box-sizing:border-box;box-shadow:var(--cttel-shadow-sm);overflow:hidden;transition:transform .22s cubic-bezier(.22,1,.36,1),box-shadow .22s ease,border-color .2s ease;}'
		. '.cttel-pcard:hover{transform:translateY(-3px);box-shadow:var(--cttel-shadow-md);border-color:var(--cttel-border-strong,rgba(20,28,38,.16));}'
		. '.cttel-pcard__link{text-decoration:none;color:inherit;display:block;}'
		. '.cttel-pcard__media{position:relative;aspect-ratio:var(--cttel-img-product,1/1);background:linear-gradient(180deg,#fafbfc 0%,#eef2f7 100%);overflow:hidden;margin:0;display:flex;align-items:center;justify-content:center;padding:.35rem;box-sizing:border-box;}'
		. '.cttel-pcard__img,.cttel-pcard__media img{width:100%;height:100%;object-fit:contain;display:block;transition:transform .35s cubic-bezier(.22,1,.36,1);}'
		. '.cttel-pcard:hover .cttel-pcard__img,.cttel-pcard:hover .cttel-pcard__media img{transform:scale(1.03);}'
		. '.cttel-pcard-badges{position:absolute;top:.55rem;inset-inline-start:.55rem;inset-inline-end:.55rem;display:flex;flex-wrap:wrap;gap:.35rem;z-index:2;justify-content:flex-start;}'
		. '.cttel-pcard-badge{font-size:.6875rem;line-height:1.2;padding:.25rem .5rem;border-radius:var(--cttel-radius-pill,999px);font-weight:700;letter-spacing:.01em;}'
		. '.cttel-pcard-badge--sale{background:#fef2f2;color:#b91c1c;border:1px solid rgba(185,28,28,.12);}'
		. '.cttel-pcard-badge--installment{background:#eff6ff;color:#1d4ed8;border:1px solid rgba(29,78,216,.12);}'
		. '.cttel-pcard__title{font-size:.9375rem;line-height:1.35;margin:0;padding:.75rem .85rem 0;font-weight:700;color:var(--cttel-text,#141c26);overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;min-height:2.55em;}'
		. '.cttel-pcard__meta{padding:0 .85rem .65rem;margin-top:auto;}'
		. '.cttel-pcard__price{font-size:1.0625rem;font-weight:800;margin:0 0 .25rem;color:var(--cttel-text);}'
		. '.cttel-pcard__price del{opacity:.5;font-weight:500;font-size:.8125rem;margin-inline-start:.35rem;}'
		. '.cttel-pcard__stock{font-size:.75rem;margin:0;color:var(--cttel-text-secondary,#5c6b7a);}'
		. '.cttel-pcard__stock.is-out-of-stock{color:var(--cttel-warning,#d97706);}'
		. '.cttel-pcard__stock.is-in-stock{color:var(--cttel-success,#0d9488);}'
		. '.cttel-pcard__actions{padding:0 .85rem .85rem;margin-top:0;}'
		. '.cttel-pcard__btn,.cttel-pcard .button{width:100%;text-align:center;min-height:44px;display:inline-flex!important;align-items:center;justify-content:center;border-radius:var(--cttel-radius-md,10px);font-size:.8125rem;font-weight:700;box-sizing:border-box;background:var(--cttel-brand-primary,#1a56db)!important;color:#fff!important;border:none!important;}'
		. '.cttel-pcard__btn:hover,.cttel-pcard .button:hover{background:var(--cttel-brand-primary-hover,#1446b8)!important;}'
		. '.cttel-products ul.products li.product .woocommerce-loop-product__title{font-size:.9375rem;line-height:1.35;margin:0;padding:.75rem .85rem 0;font-weight:700;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;}'
		. '.cttel-products ul.products li.product .price{font-size:1.0625rem;font-weight:800;margin:0;padding:0 .85rem .65rem;}'
		. '.cttel-products ul.products li.product .button{margin:.65rem .85rem .85rem;width:calc(100% - 1.7rem);}'
		. '@media (max-width:1024px){.cttel-products .wc-block-grid__products,.cttel-products ul.products{grid-template-columns:repeat(3,minmax(0,1fr))!important;}}'
		. '@media (max-width:781px){.cttel-products .wc-block-grid__products,.cttel-products ul.products{grid-template-columns:repeat(2,minmax(0,1fr))!important;}}'
		. '@media (max-width:430px){.cttel-pcard__title{font-size:.875rem;min-height:2.45em;}.cttel-pcard__price{font-size:1rem;}}';
}

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! is_front_page() && ! is_shop() && ! is_product_taxonomy() && ! is_cart() && ! is_checkout() ) {
			return;
		}
		wp_register_style( 'cttel-storefront', false, array( 'cttel-design-system' ), '2.0.0' );
		wp_enqueue_style( 'cttel-storefront' );
		wp_add_inline_style( 'cttel-storefront', cttel_storefront_inline_css() );
	},
	20
);

/** Wrap classic shortcode product cards with cttel-pcard class. */
add_filter(
	'woocommerce_post_class',
	static function ( $classes, $product ) {
		if ( is_front_page() || is_shop() || is_product_taxonomy() ) {
			$classes[] = 'cttel-pcard';
		}
		return $classes;
	},
	10,
	2
);
