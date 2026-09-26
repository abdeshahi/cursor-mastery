<?php
/**
 * CTTEL Homepage sections — approved mockup implementation.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

function cttel_home_cat_url( string $slug, string $fallback_path ): string {
	$term = get_term_by( 'slug', $slug, 'product_cat' );
	if ( $term instanceof WP_Term ) {
		return get_term_link( $term );
	}
	return home_url( $fallback_path );
}

function cttel_home_hero_image_html(): string {
	$attach_id = absint( get_option( 'cttel_hero_media_id', 0 ) );
	if ( $attach_id <= 0 ) {
		$attach_id = absint( get_option( 'cttel_product_placeholder_id', 0 ) );
	}
	if ( $attach_id > 0 ) {
		$img = wp_get_attachment_image(
			$attach_id,
			'1536x1536',
			false,
			array(
				'class'   => 'cttel-v2-hero__photo',
				'loading' => 'eager',
				'alt'     => '',
			)
		);
		if ( $img ) {
			return $img;
		}
	}
	return '<div class="cttel-v2-hero__photo cttel-v2-hero__photo--fallback" aria-hidden="true"></div>';
}

function cttel_shortcode_hero(): string {
	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-hero">
		<div class="cttel-container">
			<div class="cttel-v2-hero__card cttel-v2-hero__card--editorial">
				<div class="cttel-v2-hero__media">
					<?php echo cttel_home_hero_image_html(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<div class="cttel-v2-hero__media-scrim" aria-hidden="true"></div>
				</div>
				<div class="cttel-v2-hero__copy">
					<p class="cttel-v2-hero__eyebrow">سری جدید</p>
					<h1 class="cttel-v2-hero__title">فراتر از انتظار</h1>
					<p class="cttel-v2-hero__lead">تجربه خرید مطمئن، پشتیبانی فروشگاه و امکان خرید اقساطی از CTTEL</p>
					<div class="cttel-v2-hero__actions">
						<a class="cttel-v2-btn cttel-v2-btn--primary cttel-v2-btn__chev" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">مشاهده محصولات</a>
						<a class="cttel-v2-btn cttel-v2-btn--outline-light cttel-v2-btn__chev" href="<?php echo esc_url( home_url( '/installment/' ) ); ?>">خرید اقساطی</a>
					</div>
				</div>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_hero', 'cttel_shortcode_hero' );

function cttel_shortcode_service_rail(): string {
	$items = array(
		array(
			'label' => 'خرید اقساطی',
			'desc'  => 'ساده و سریع',
			'url'   => home_url( '/installment/' ),
			'icon'  => 'installment',
		),
		array(
			'label' => 'گوشی کارکرده',
			'desc'  => 'خرید و فروش مطمئن',
			'url'   => home_url( '/used-phone/' ),
			'icon'  => 'used',
		),
		array(
			'label' => 'درخواست تأمین',
			'desc'  => 'مدل موردنظر را پیدا می‌کنیم',
			'url'   => home_url( '/used-phone-request/' ),
			'icon'  => 'sourcing',
		),
		array(
			'label' => 'پشتیبانی',
			'desc'  => 'قبل و بعد از خرید',
			'url'   => home_url( '/my-account/' ),
			'icon'  => 'support',
		),
	);

	ob_start();
	?>
	<nav class="cttel-v2 cttel-v2-service-rail" aria-label="<?php esc_attr_e( 'دسترسی سریع', 'cttel-store' ); ?>">
		<div class="cttel-container">
			<div class="cttel-v2-service-rail__strip">
				<div class="cttel-v2-service-rail__grid">
					<?php foreach ( $items as $item ) : ?>
						<a class="cttel-v2-service-rail__item" href="<?php echo esc_url( $item['url'] ); ?>">
							<span class="cttel-v2-service-rail__icon cttel-v2-service-rail__icon--<?php echo esc_attr( $item['icon'] ); ?>" aria-hidden="true"></span>
							<span class="cttel-v2-service-rail__text">
								<span class="cttel-v2-service-rail__label"><?php echo esc_html( $item['label'] ); ?></span>
								<span class="cttel-v2-service-rail__desc"><?php echo esc_html( $item['desc'] ); ?></span>
							</span>
						</a>
					<?php endforeach; ?>
				</div>
			</div>
		</div>
	</nav>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_service_rail', 'cttel_shortcode_service_rail' );

function cttel_mosaic_tile_image( array $tile ): string {
	if ( ! empty( $tile['slug'] ) ) {
		$term = get_term_by( 'slug', $tile['slug'], 'product_cat' );
		if ( $term instanceof WP_Term ) {
			$thumb_id = (int) get_term_meta( $term->term_id, 'thumbnail_id', true );
			if ( $thumb_id > 0 ) {
				return wp_get_attachment_image(
					$thumb_id,
					'medium_large',
					false,
					array(
						'class'   => 'cttel-v2-mosaic__img',
						'loading' => 'lazy',
						'alt'     => '',
					)
				);
			}
		}
	}
	return '<span class="cttel-v2-mosaic__placeholder cttel-v2-mosaic__placeholder--' . esc_attr( $tile['theme'] ?? 'default' ) . '" aria-hidden="true"></span>';
}

function cttel_shortcode_category_mosaic(): string {
	$tiles = array(
		array(
			'size'  => 'large',
			'theme' => 'mobile',
			'title' => 'موبایل',
			'desc'  => 'جدیدترین گوشی‌های هوشمند',
			'slug'  => 'mobile',
			'path'  => '/product-category/mobile/',
		),
		array(
			'size'  => 'large',
			'theme' => 'accessories',
			'title' => 'لوازم جانبی',
			'desc'  => 'همراه بهتر برای دستگاه‌های شما',
			'slug'  => 'accessories',
			'path'  => '/product-category/accessories/',
		),
		array(
			'size'  => 'small',
			'theme' => 'headphones',
			'title' => 'هندزفری',
			'desc'  => 'صدا و تماس',
			'slug'  => 'headphones',
			'path'  => '/product-category/headphones/',
		),
		array(
			'size'  => 'small',
			'theme' => 'watch',
			'title' => 'ساعت هوشمند',
			'desc'  => 'پوشیدنی‌های هوشمند',
			'slug'  => 'smartwatch',
			'path'  => '/product-category/smartwatch/',
		),
		array(
			'size'  => 'small',
			'theme' => 'used',
			'title' => 'گوشی کارکرده',
			'desc'  => 'موجودی تأیید‌شده',
			'url'   => home_url( '/used-phone/' ),
		),
		array(
			'size'  => 'small',
			'theme' => 'installment',
			'title' => 'خرید اقساطی',
			'desc'  => 'مسیر خرید منعطف',
			'url'   => home_url( '/installment/' ),
		),
	);

	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-section cttel-v2-mosaic">
		<div class="cttel-container">
			<div class="cttel-v2-mosaic__grid">
				<?php foreach ( $tiles as $tile ) : ?>
					<?php
					$url = ! empty( $tile['url'] )
						? $tile['url']
						: cttel_home_cat_url( $tile['slug'], $tile['path'] );
					?>
					<a class="cttel-v2-mosaic__tile cttel-v2-mosaic__tile--<?php echo esc_attr( $tile['size'] ); ?> cttel-v2-mosaic__tile--<?php echo esc_attr( $tile['theme'] ); ?>" href="<?php echo esc_url( $url ); ?>">
						<div class="cttel-v2-mosaic__visual">
							<?php echo cttel_mosaic_tile_image( $tile ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
							<span class="cttel-v2-mosaic__scrim" aria-hidden="true"></span>
						</div>
						<div class="cttel-v2-mosaic__copy">
							<h3 class="cttel-v2-mosaic__title"><?php echo esc_html( $tile['title'] ); ?></h3>
							<p class="cttel-v2-mosaic__desc"><?php echo esc_html( $tile['desc'] ); ?></p>
						</div>
						<span class="cttel-v2-mosaic__go" aria-hidden="true">‹</span>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_category_mosaic', 'cttel_shortcode_category_mosaic' );

function cttel_home_section_promo_image( string $option_key, string $css_class ): string {
	$attach_id = absint( get_option( $option_key, 0 ) );
	if ( $attach_id <= 0 ) {
		return '';
	}
	return wp_get_attachment_image(
		$attach_id,
		'medium_large',
		false,
		array(
			'class'   => $css_class,
			'loading' => 'lazy',
			'alt'     => '',
		)
	);
}

function cttel_shortcode_used_phone_banner(): string {
	$visual = cttel_home_section_promo_image( 'cttel_used_banner_media_id', 'cttel-v2-used-banner__photo' );
	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-used-banner">
		<div class="cttel-container cttel-v2-used-banner__inner">
			<div class="cttel-v2-used-banner__copy">
				<p class="cttel-v2-eyebrow cttel-v2-used-banner__eyebrow">CTTEL</p>
				<h2 class="cttel-v2-used-banner__title">گوشی کارکرده</h2>
				<p class="cttel-v2-used-banner__lead">کیفیت بالا، قیمت بهتر — موجودی فروشگاه یا درخواست تأمین اختصاصی</p>
				<a class="cttel-v2-btn cttel-v2-btn--outline-dark cttel-v2-btn__chev" href="<?php echo esc_url( home_url( '/used-phone/' ) ); ?>">مشاهده و درخواست</a>
			</div>
			<div class="cttel-v2-used-banner__visual" aria-hidden="true">
				<?php echo $visual; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_used_phone_banner', 'cttel_shortcode_used_phone_banner' );

/** @deprecated Use cttel_used_phone_banner — kept for rollback. */
add_shortcode( 'cttel_used_phone_experience', 'cttel_shortcode_used_phone_banner' );

function cttel_shortcode_installment_campaign(): string {
	$visual = cttel_home_section_promo_image( 'cttel_installment_campaign_media_id', 'cttel-v2-installment-light__photo' );
	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-installment-light" aria-labelledby="cttel-installment-title">
		<div class="cttel-container cttel-v2-installment-light__inner">
			<div class="cttel-v2-installment-light__visual" aria-hidden="true">
				<?php echo $visual; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
			</div>
			<div class="cttel-v2-installment-light__copy">
				<p class="cttel-v2-eyebrow">خرید اقساطی</p>
				<h2 id="cttel-installment-title" class="cttel-v2-installment-light__title">خرید اقساطی موبایل و لوازم دیجیتال</h2>
				<p class="cttel-v2-installment-light__lead">مسیر مشخص انتخاب محصول و ثبت درخواست — بدون اطلاعات مالی ساختگی در صفحه اصلی.</p>
				<ul class="cttel-v2-installment-light__chips">
					<li>سریع</li>
					<li>مطمئن</li>
					<li>شفاف</li>
				</ul>
				<a class="cttel-v2-btn cttel-v2-btn--primary cttel-v2-btn__chev" href="<?php echo esc_url( home_url( '/installment/' ) ); ?>">مشاهده شرایط</a>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_installment_campaign', 'cttel_shortcode_installment_campaign' );

function cttel_shortcode_trust_bar(): string {
	$items = array(
		array( 'icon' => 'ship', 'title' => 'ارسال سریع', 'desc' => 'ارسال به سراسر ایران' ),
		array( 'icon' => 'shield', 'title' => 'ضمانت اصالت', 'desc' => 'کالای اورجینال' ),
		array( 'icon' => 'pay', 'title' => 'پرداخت امن', 'desc' => 'درگاه معتبر' ),
		array( 'icon' => 'support', 'title' => 'پشتیبانی تخصصی', 'desc' => 'همراه شما' ),
	);

	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-trust-bar" aria-label="<?php esc_attr_e( 'مزایای خرید', 'cttel-store' ); ?>">
		<div class="cttel-container cttel-v2-trust-bar__grid">
			<?php foreach ( $items as $item ) : ?>
				<div class="cttel-v2-trust-bar__item">
					<span class="cttel-v2-trust-bar__icon cttel-v2-trust-bar__icon--<?php echo esc_attr( $item['icon'] ); ?>" aria-hidden="true"></span>
					<div>
						<strong class="cttel-v2-trust-bar__title"><?php echo esc_html( $item['title'] ); ?></strong>
						<span class="cttel-v2-trust-bar__desc"><?php echo esc_html( $item['desc'] ); ?></span>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_trust_bar', 'cttel_shortcode_trust_bar' );

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( function_exists( 'cttel_is_dedicated_homepage' ) && cttel_is_dedicated_homepage() ) {
			return;
		}
		if ( ! is_front_page() ) {
			return;
		}
		$path = __DIR__ . '/cttel-home-v2.css';
		if ( ! file_exists( $path ) ) {
			return;
		}
		wp_register_style( 'cttel-home-v2', false, array( 'cttel-design-system' ), '4.0.0' );
		wp_enqueue_style( 'cttel-home-v2' );
		wp_add_inline_style( 'cttel-home-v2', (string) file_get_contents( $path ) );
	},
	25
);
