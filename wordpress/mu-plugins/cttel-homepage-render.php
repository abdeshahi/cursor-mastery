<?php
/**
 * CTTEL homepage render — sections only (no shortcodes / no Gutenberg).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Preview/staging line-art assets — never use as customer-facing homepage photography. */
function cttel_is_preview_attachment( int $attach_id ): bool {
	if ( $attach_id <= 0 ) {
		return true;
	}
	$placeholder = absint( get_option( 'cttel_product_placeholder_id', 0 ) );
	if ( $placeholder > 0 && $attach_id === $placeholder ) {
		return true;
	}
	$post = get_post( $attach_id );
	if ( ! $post instanceof WP_Post ) {
		return true;
	}
	$preview_slugs = array(
		'hero-mobile-gadgets',
		'cttel-hero-mobile-gadgets',
		'product-placeholder',
		'cttel-product-placeholder',
		'cat-mobile',
		'cttel-cat-mobile',
		'cat-headphones',
		'cttel-cat-headphones',
		'cat-smartwatch',
		'cttel-cat-smartwatch',
		'cat-accessories',
		'cttel-cat-accessories',
		'cat-gadgets',
		'cttel-cat-gadgets',
		'cat-installment',
		'cttel-cat-installment',
	);
	if ( in_array( $post->post_name, $preview_slugs, true ) ) {
		return true;
	}
	return 0 === strpos( $post->post_name, 'cttel-' ) && false !== strpos( $post->post_name, 'placeholder' );
}

function cttel_home_cat_link( string $slug, string $path ): string {
	$term = get_term_by( 'slug', $slug, 'product_cat' );
	if ( $term instanceof WP_Term ) {
		return get_term_link( $term );
	}
	return home_url( $path );
}

/** Product has a non-placeholder featured image. */
function cttel_product_has_real_thumbnail( WC_Product $product ): bool {
	$thumb_id = $product->get_image_id();
	if ( $thumb_id <= 0 ) {
		return false;
	}
	return ! cttel_is_preview_attachment( $thumb_id );
}

/**
 * @return WC_Product[]
 */
function cttel_homepage_products( int $limit = 4 ): array {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return array();
	}
	$args = array(
		'limit'    => $limit * 4,
		'status'   => 'publish',
		'featured' => true,
		'orderby'  => 'date',
		'order'    => 'DESC',
	);
	$found = wc_get_products( $args );
	$out   = array();
	foreach ( $found as $product ) {
		if ( ! $product instanceof WC_Product || ! cttel_product_has_real_thumbnail( $product ) ) {
			continue;
		}
		$out[] = $product;
		if ( count( $out ) >= $limit ) {
			break;
		}
	}
	if ( empty( $out ) ) {
		unset( $args['featured'] );
		$found = wc_get_products( $args );
		foreach ( $found as $product ) {
			if ( ! $product instanceof WC_Product || ! cttel_product_has_real_thumbnail( $product ) ) {
				continue;
			}
			$out[] = $product;
			if ( count( $out ) >= $limit ) {
				break;
			}
		}
	}
	return $out;
}

function cttel_homepage_attachment_img( int $attach_id, string $size, string $class ): string {
	if ( cttel_is_preview_attachment( $attach_id ) ) {
		return '';
	}
	return wp_get_attachment_image(
		$attach_id,
		$size,
		false,
		array(
			'class'   => $class,
			'loading' => 'lazy',
			'alt'     => '',
		)
	);
}

function cttel_homepage_term_image( string $slug, string $size = 'medium_large' ): string {
	$term = get_term_by( 'slug', $slug, 'product_cat' );
	if ( ! $term instanceof WP_Term ) {
		return '';
	}
	$thumb_id = (int) get_term_meta( $term->term_id, 'thumbnail_id', true );
	if ( $thumb_id <= 0 ) {
		return '';
	}
	if ( cttel_is_preview_attachment( $thumb_id ) ) {
		return '';
	}
	return wp_get_attachment_image(
		$thumb_id,
		$size,
		false,
		array(
			'class'   => 'cttel-home-mosaic__photo',
			'loading' => 'lazy',
			'alt'     => '',
		)
	);
}

function cttel_homepage_render_all(): void {
	cttel_homepage_render_hero();
	cttel_homepage_render_service_rail();
	cttel_homepage_render_mosaic();
	cttel_homepage_render_products();
	cttel_homepage_render_used_phone();
	cttel_homepage_render_installment();
	cttel_homepage_render_trust();
}

function cttel_homepage_render_hero(): void {
	$hero_id = absint( get_option( 'cttel_hero_media_id', 0 ) );
	$hero_img = cttel_homepage_attachment_img( $hero_id, 'large', 'cttel-home-hero__img' );
	$has_media = '' !== $hero_img;
	?>
	<section class="cttel-home-hero" aria-labelledby="cttel-home-hero-title">
		<div class="cttel-home-wrap">
			<div class="cttel-home-hero__card<?php echo $has_media ? ' cttel-home-hero__card--has-media' : ''; ?>">
				<?php if ( $has_media ) : ?>
					<div class="cttel-home-hero__media"><?php echo $hero_img; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
				<?php endif; ?>
				<div class="cttel-home-hero__body">
					<p class="cttel-home-hero__eyebrow">سری جدید</p>
					<h1 id="cttel-home-hero-title" class="cttel-home-hero__title">فراتر از انتظار</h1>
					<p class="cttel-home-hero__lead">تجربه خرید مطمئن، پشتیبانی فروشگاه و امکان خرید اقساطی از CTTEL</p>
					<div class="cttel-home-hero__actions">
						<a class="cttel-home-btn cttel-home-btn--primary" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">مشاهده محصولات</a>
						<a class="cttel-home-btn cttel-home-btn--ghost" href="<?php echo esc_url( home_url( '/installment/' ) ); ?>">خرید اقساطی</a>
					</div>
				</div>
			</div>
		</div>
	</section>
	<?php
}

function cttel_homepage_render_service_rail(): void {
	$items = array(
		array( 'label' => 'خرید اقساطی', 'desc' => 'ساده و سریع', 'url' => home_url( '/installment/' ), 'icon' => 'installment' ),
		array( 'label' => 'گوشی کارکرده', 'desc' => 'خرید و فروش مطمئن', 'url' => home_url( '/used-phone/' ), 'icon' => 'used' ),
		array( 'label' => 'درخواست تأمین', 'desc' => 'مدل موردنظر را پیدا می‌کنیم', 'url' => home_url( '/used-phone-request/' ), 'icon' => 'supply' ),
		array( 'label' => 'پشتیبانی', 'desc' => 'قبل و بعد از خرید', 'url' => home_url( '/my-account/' ), 'icon' => 'support' ),
	);
	?>
	<nav class="cttel-home-rail" aria-label="<?php esc_attr_e( 'دسترسی سریع', 'cttel-store' ); ?>">
		<div class="cttel-home-wrap">
			<div class="cttel-home-rail__strip">
				<?php foreach ( $items as $item ) : ?>
					<a class="cttel-home-rail__cell" href="<?php echo esc_url( $item['url'] ); ?>">
						<span class="cttel-home-rail__icon cttel-home-rail__icon--<?php echo esc_attr( $item['icon'] ); ?>" aria-hidden="true"></span>
						<span class="cttel-home-rail__label"><?php echo esc_html( $item['label'] ); ?></span>
						<span class="cttel-home-rail__desc"><?php echo esc_html( $item['desc'] ); ?></span>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	</nav>
	<?php
}

function cttel_homepage_render_mosaic(): void {
	$tiles = array(
		array( 'large', 'mobile', 'موبایل', 'جدیدترین گوشی‌های هوشمند', 'mobile', '/product-category/mobile/' ),
		array( 'large', 'accessories', 'لوازم جانبی', 'همراه بهتر برای دستگاه‌های شما', 'accessories', '/product-category/accessories/' ),
		array( 'small', 'headphones', 'هندزفری', 'صدا و تماس', 'headphones', '/product-category/headphones/' ),
		array( 'small', 'watch', 'ساعت هوشمند', 'پوشیدنی‌های هوشمند', 'smartwatch', '/product-category/smartwatch/' ),
		array( 'small', 'used', 'گوشی کارکرده', 'موجودی تأیید‌شده', '', '/used-phone/' ),
		array( 'small', 'installment', 'خرید اقساطی', 'مسیر خرید منعطف', '', '/installment/' ),
	);
	?>
	<section class="cttel-home-mosaic" aria-label="<?php esc_attr_e( 'دسته‌بندی‌ها', 'cttel-store' ); ?>">
		<div class="cttel-home-wrap">
			<div class="cttel-home-mosaic__grid">
				<?php foreach ( $tiles as $tile ) : ?>
					<?php
					list( $size, $theme, $title, $desc, $slug, $path ) = $tile;
					$url = $slug ? cttel_home_cat_link( $slug, $path ) : home_url( $path );
					$img = $slug ? cttel_homepage_term_image( $slug ) : '';
					?>
					<a class="cttel-home-mosaic__tile cttel-home-mosaic__tile--<?php echo esc_attr( $size ); ?> cttel-home-mosaic__tile--<?php echo esc_attr( $theme ); ?><?php echo $img ? ' cttel-home-mosaic__tile--photo' : ''; ?>" href="<?php echo esc_url( $url ); ?>">
						<?php if ( $img ) : ?>
							<div class="cttel-home-mosaic__photo-wrap"><?php echo $img; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
						<?php endif; ?>
						<div class="cttel-home-mosaic__copy">
							<h2 class="cttel-home-mosaic__title"><?php echo esc_html( $title ); ?></h2>
							<p class="cttel-home-mosaic__desc"><?php echo esc_html( $desc ); ?></p>
						</div>
						<span class="cttel-home-mosaic__arrow" aria-hidden="true">‹</span>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<?php
}

function cttel_homepage_render_products(): void {
	$products = cttel_homepage_products( 4 );
	?>
	<section class="cttel-home-products" aria-labelledby="cttel-home-products-title">
		<div class="cttel-home-wrap">
			<div class="cttel-home-products__head">
				<h2 id="cttel-home-products-title" class="cttel-home-products__title">پیشنهادهای ویژه CTTEL</h2>
				<a class="cttel-home-products__all" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">مشاهده همه</a>
			</div>
			<?php if ( empty( $products ) ) : ?>
				<p class="cttel-home-products__empty"><?php esc_html_e( 'به‌زودی محصولات منتخب با تصویر واقعی در این بخش نمایش داده می‌شوند.', 'cttel-store' ); ?></p>
			<?php else : ?>
				<ul class="cttel-home-products__grid">
					<?php foreach ( $products as $product ) : ?>
						<?php echo cttel_homepage_product_card( $product ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<?php endforeach; ?>
				</ul>
			<?php endif; ?>
		</div>
	</section>
	<?php
}

function cttel_homepage_product_card( WC_Product $product ): string {
	$thumb_id = $product->get_image_id();
	$image    = wp_get_attachment_image(
		$thumb_id,
		'woocommerce_thumbnail',
		false,
		array(
			'class'   => 'cttel-home-product__img',
			'loading' => 'lazy',
			'alt'     => $product->get_name(),
		)
	);
	ob_start();
	?>
	<li class="cttel-home-product">
		<a class="cttel-home-product__link" href="<?php echo esc_url( $product->get_permalink() ); ?>">
			<div class="cttel-home-product__media"><?php echo $image; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
			<h3 class="cttel-home-product__name"><?php echo esc_html( $product->get_name() ); ?></h3>
		</a>
		<div class="cttel-home-product__price price"><?php echo wp_kses_post( $product->get_price_html() ); ?></div>
		<a href="<?php echo esc_url( $product->add_to_cart_url() ); ?>" class="cttel-home-product__cart button add_to_cart_button product_type_<?php echo esc_attr( $product->get_type() ); ?>" data-product_id="<?php echo esc_attr( (string) $product->get_id() ); ?>"><?php echo esc_html( $product->add_to_cart_text() ); ?></a>
	</li>
	<?php
	return (string) ob_get_clean();
}

function cttel_homepage_render_used_phone(): void {
	$media_id = absint( get_option( 'cttel_used_banner_media_id', 0 ) );
	$photo    = cttel_homepage_attachment_img( $media_id, 'medium_large', 'cttel-home-used__photo' );
	?>
	<section class="cttel-home-used">
		<div class="cttel-home-wrap">
			<div class="cttel-home-used__panel<?php echo $photo ? ' cttel-home-used__panel--photo' : ''; ?>">
				<div class="cttel-home-used__copy">
					<h2 class="cttel-home-used__title">گوشی کارکرده</h2>
					<p class="cttel-home-used__lead">کیفیت بالا، قیمت بهتر — موجودی فروشگاه یا درخواست تأمین اختصاصی</p>
					<a class="cttel-home-btn cttel-home-btn--ghost" href="<?php echo esc_url( home_url( '/used-phone/' ) ); ?>">مشاهده و درخواست</a>
				</div>
				<?php if ( $photo ) : ?>
					<div class="cttel-home-used__media"><?php echo $photo; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
				<?php endif; ?>
			</div>
		</div>
	</section>
	<?php
}

function cttel_homepage_render_installment(): void {
	$media_id = absint( get_option( 'cttel_installment_campaign_media_id', 0 ) );
	$photo    = cttel_homepage_attachment_img( $media_id, 'medium_large', 'cttel-home-installment__photo' );
	?>
	<section class="cttel-home-installment" aria-labelledby="cttel-home-installment-title">
		<div class="cttel-home-wrap">
			<div class="cttel-home-installment__panel">
				<?php if ( $photo ) : ?>
					<div class="cttel-home-installment__media"><?php echo $photo; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
				<?php endif; ?>
				<div class="cttel-home-installment__copy">
					<h2 id="cttel-home-installment-title" class="cttel-home-installment__title">خرید اقساطی موبایل و لوازم دیجیتال</h2>
					<p class="cttel-home-installment__lead">مسیر مشخص انتخاب محصول و ثبت درخواست — اطلاعات مالی فقط در صفحه اقساط.</p>
					<a class="cttel-home-btn cttel-home-btn--primary" href="<?php echo esc_url( home_url( '/installment/' ) ); ?>">مشاهده شرایط</a>
				</div>
			</div>
		</div>
	</section>
	<?php
}

function cttel_homepage_render_trust(): void {
	$items = array(
		array( 'ship', 'ارسال سریع', 'ارسال به سراسر ایران' ),
		array( 'shield', 'ضمانت اصالت', 'کالای اورجینال' ),
		array( 'pay', 'پرداخت امن', 'درگاه معتبر' ),
		array( 'support', 'پشتیبانی تخصصی', 'همراه شما' ),
	);
	?>
	<section class="cttel-home-trust" aria-label="<?php esc_attr_e( 'مزایای خرید', 'cttel-store' ); ?>">
		<div class="cttel-home-wrap">
			<ul class="cttel-home-trust__list">
				<?php foreach ( $items as $item ) : ?>
					<li class="cttel-home-trust__item">
						<span class="cttel-home-trust__icon cttel-home-trust__icon--<?php echo esc_attr( $item[0] ); ?>" aria-hidden="true"></span>
						<span class="cttel-home-trust__text">
							<strong><?php echo esc_html( $item[1] ); ?></strong>
							<span><?php echo esc_html( $item[2] ); ?></span>
						</span>
					</li>
				<?php endforeach; ?>
			</ul>
		</div>
	</section>
	<?php
}
