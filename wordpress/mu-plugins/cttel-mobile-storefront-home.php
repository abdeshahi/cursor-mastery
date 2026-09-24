<?php
/**
 * Mobile storefront homepage — simplified ecommerce-first layout.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

add_filter(
	'template_include',
	static function ( string $template ): string {
		if ( ! is_front_page() || is_home() ) {
			return $template;
		}
		$custom = __DIR__ . '/templates/cttel-mobile-front.php';
		return is_readable( $custom ) ? $custom : $template;
	},
	101
);

add_filter(
	'the_content',
	static function ( string $content ): string {
		if ( is_front_page() && ! is_home() && in_the_loop() && is_main_query() ) {
			return '';
		}
		return $content;
	},
	1
);

/**
 * Top-level product categories for homepage rail.
 *
 * @return WP_Term[]
 */
function cttel_ms_home_parent_categories(): array {
	if ( ! function_exists( 'cttel_get_quick_category_terms' ) ) {
		$exclude = array_filter( array( (int) get_option( 'default_product_cat', 0 ) ) );
		$terms   = get_terms(
			array(
				'taxonomy'   => 'product_cat',
				'hide_empty' => false,
				'parent'     => 0,
				'exclude'    => $exclude,
			)
		);
		if ( is_wp_error( $terms ) || empty( $terms ) ) {
			return array();
		}
		return $terms;
	}
	return cttel_get_quick_category_terms();
}

/**
 * @return WC_Product[]
 */
function cttel_ms_home_products( int $limit = 8 ): array {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return array();
	}
	$queries = array(
		array(
			'limit'    => $limit * 3,
			'status'   => 'publish',
			'on_sale'  => true,
			'orderby'  => 'date',
			'order'    => 'DESC',
		),
		array(
			'limit'    => $limit * 3,
			'status'   => 'publish',
			'featured' => true,
			'orderby'  => 'date',
			'order'    => 'DESC',
		),
		array(
			'limit'   => $limit * 3,
			'status'  => 'publish',
			'orderby' => 'date',
			'order'   => 'DESC',
		),
	);
	foreach ( $queries as $args ) {
		$found = wc_get_products( $args );
		$out   = array();
		foreach ( $found as $product ) {
			if ( ! $product instanceof WC_Product ) {
				continue;
			}
			$out[] = $product;
			if ( count( $out ) >= $limit ) {
				return $out;
			}
		}
		if ( ! empty( $out ) ) {
			return $out;
		}
	}
	return array();
}

function cttel_ms_home_render(): void {
	cttel_ms_home_render_hero();
	cttel_ms_home_render_category_rail();
	cttel_ms_home_render_products();
	cttel_ms_home_render_installment();
	cttel_ms_home_render_trust();
}

function cttel_ms_home_render_hero(): void {
	$hero_id = absint( get_option( 'cttel_hero_media_id', 0 ) );
	$hero    = '';
	if ( $hero_id > 0 ) {
		$hero = wp_get_attachment_image(
			$hero_id,
			'large',
			false,
			array(
				'class'   => 'cttel-ms-hero__img',
				'loading' => 'eager',
				'alt'     => '',
			)
		);
	}
	$shop = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
	?>
	<section class="cttel-ms-hero" aria-labelledby="cttel-ms-hero-title">
		<div class="cttel-ms-hero__card">
			<?php if ( $hero ) : ?>
				<div class="cttel-ms-hero__media"><?php echo $hero; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
			<?php else : ?>
				<div class="cttel-ms-hero__media cttel-ms-hero__media--brand" aria-hidden="true"></div>
			<?php endif; ?>
			<div class="cttel-ms-hero__body">
				<h1 id="cttel-ms-hero-title" class="cttel-ms-hero__title">فروشگاه CTTEL</h1>
				<p class="cttel-ms-hero__lead">موبایل، لوازم جانبی و کالای دیجیتال با ارسال سریع و پشتیبانی فروشگاه</p>
				<a class="cttel-ms-btn cttel-ms-btn--primary" href="<?php echo esc_url( $shop ); ?>">مشاهده فروشگاه</a>
			</div>
		</div>
	</section>
	<?php
}

function cttel_ms_home_render_category_rail(): void {
	$terms = cttel_ms_home_parent_categories();
	if ( empty( $terms ) ) {
		return;
	}
	$terms = array_slice( $terms, 0, 8 );
	?>
	<nav class="cttel-ms-cat-rail" aria-label="<?php esc_attr_e( 'دسته‌بندی محصولات', 'cttel-store' ); ?>">
		<ul class="cttel-ms-cat-rail__list">
			<?php foreach ( $terms as $term ) : ?>
				<?php if ( ! $term instanceof WP_Term ) {
					continue;
				} ?>
				<li>
					<a class="cttel-ms-cat-rail__item" href="<?php echo esc_url( get_term_link( $term ) ); ?>">
						<span class="cttel-ms-cat-rail__icon"><?php echo cttel_mobile_storefront_category_icon( $term ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
						<span class="cttel-ms-cat-rail__label"><?php echo esc_html( $term->name ); ?></span>
					</a>
				</li>
			<?php endforeach; ?>
		</ul>
	</nav>
	<?php
}

function cttel_ms_home_render_products(): void {
	$products = cttel_ms_home_products( 8 );
	$shop     = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
	?>
	<section class="cttel-ms-products" aria-labelledby="cttel-ms-products-title">
		<div class="cttel-ms-section-head">
			<h2 id="cttel-ms-products-title" class="cttel-ms-section-head__title">جدیدترین محصولات</h2>
			<a class="cttel-ms-section-head__link" href="<?php echo esc_url( $shop ); ?>">مشاهده همه</a>
		</div>
		<?php if ( empty( $products ) ) : ?>
			<p class="cttel-ms-empty"><?php esc_html_e( 'محصولی برای نمایش یافت نشد.', 'cttel-store' ); ?></p>
		<?php else : ?>
			<ul class="cttel-ms-products__grid">
				<?php foreach ( $products as $product ) : ?>
					<?php echo cttel_ms_product_card( $product ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				<?php endforeach; ?>
			</ul>
		<?php endif; ?>
	</section>
	<?php
}

function cttel_ms_product_card( WC_Product $product ): string {
	$image = cttel_ms_product_card_image_html( $product, 'cttel-ms-pcard__img' );

	ob_start();
	?>
	<li class="cttel-ms-pcard">
		<a class="cttel-ms-pcard__link" href="<?php echo esc_url( $product->get_permalink() ); ?>">
			<div class="cttel-ms-pcard__media"><?php echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
			<h3 class="cttel-ms-pcard__name"><?php echo esc_html( $product->get_name() ); ?></h3>
		</a>
		<div class="cttel-ms-pcard__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
	</li>
	<?php
	return (string) ob_get_clean();
}

function cttel_ms_home_render_installment(): void {
	$url = home_url( '/installment/' );
	if ( function_exists( 'cttel_installment_default_url' ) ) {
		$url = cttel_installment_default_url();
	}
	?>
	<section class="cttel-ms-installment">
		<a class="cttel-ms-installment__banner" href="<?php echo esc_url( $url ); ?>">
			<span class="cttel-ms-installment__title">خرید اقساطی</span>
			<span class="cttel-ms-installment__desc">شرایط و ثبت درخواست در صفحه اختصاصی</span>
		</a>
	</section>
	<?php
}

function cttel_ms_home_render_trust(): void {
	$items = array(
		'پشتیبانی فروشگاه',
		'ضمانت اصالت کالا',
		'پرداخت امن',
		'ارسال به سراسر ایران',
	);
	?>
	<section class="cttel-ms-trust" aria-label="<?php esc_attr_e( 'مزایای خرید', 'cttel-store' ); ?>">
		<ul class="cttel-ms-trust__list">
			<?php foreach ( $items as $label ) : ?>
				<li><?php echo esc_html( $label ); ?></li>
			<?php endforeach; ?>
		</ul>
	</section>
	<?php
}
