<?php
/**
 * CTTEL Homepage v2 sections — visual composition shortcodes only.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Resolve product category link by slug. */
function cttel_home_cat_url( string $slug, string $fallback_path ): string {
	$term = get_term_by( 'slug', $slug, 'product_cat' );
	if ( $term instanceof WP_Term ) {
		return get_term_link( $term );
	}
	return home_url( $fallback_path );
}

/** Service rail below hero. */
function cttel_shortcode_service_rail(): string {
	$items = array(
		array(
			'label' => 'خرید اقساطی',
			'desc'  => 'انتخاب محصول و ثبت درخواست',
			'url'   => home_url( '/installment/' ),
			'icon'  => 'installment',
		),
		array(
			'label' => 'گوشی کارکرده',
			'desc'  => 'موجودی تأیید‌شده',
			'url'   => home_url( '/used-phone/' ),
			'icon'  => 'used',
		),
		array(
			'label' => 'درخواست تأمین گوشی',
			'desc'  => 'پیدا کردن مدل موردنظر',
			'url'   => home_url( '/used-phone-request/' ),
			'icon'  => 'sourcing',
		),
		array(
			'label' => 'لوازم جانبی',
			'desc'  => 'کاور، شارژر، صدا',
			'url'   => cttel_home_cat_url( 'accessories', '/product-category/accessories/' ),
			'icon'  => 'accessories',
		),
	);

	ob_start();
	?>
	<nav class="cttel-v2 cttel-v2-service-rail" aria-label="<?php esc_attr_e( 'دسترسی سریع', 'cttel-store' ); ?>">
		<div class="cttel-container cttel-v2-service-rail__inner">
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
	</nav>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_service_rail', 'cttel_shortcode_service_rail' );

/** Editorial category mosaic — asymmetric tiles, no emoji. */
function cttel_shortcode_category_mosaic(): string {
	$tiles = array(
		array(
			'size'  => 'large',
			'title' => 'موبایل',
			'desc'  => 'جدیدترین اسمارت‌فون‌ها و پرچمدارها',
			'slug'  => 'mobile',
			'path'  => '/product-category/mobile/',
		),
		array(
			'size'  => 'medium',
			'title' => 'لوازم جانبی',
			'desc'  => 'جانبی اصل و سازگار',
			'slug'  => 'accessories',
			'path'  => '/product-category/accessories/',
		),
		array(
			'size'  => 'medium',
			'title' => 'گوشی کارکرده',
			'desc'  => 'کارکرده با شفافیت وضعیت',
			'slug'  => '',
			'path'  => '/used-phone/',
			'url'   => home_url( '/used-phone/' ),
		),
		array(
			'size'  => 'small',
			'title' => 'هندزفری',
			'desc'  => 'صدا و تماس',
			'slug'  => 'headphones',
			'path'  => '/product-category/headphones/',
		),
		array(
			'size'  => 'small',
			'title' => 'ساعت هوشمند',
			'desc'  => 'پوشیدنی‌های هوشمند',
			'slug'  => 'smartwatch',
			'path'  => '/product-category/smartwatch/',
		),
		array(
			'size'  => 'small',
			'title' => 'خرید اقساطی',
			'desc'  => 'مسیر خرید منعطف',
			'slug'  => '',
			'path'  => '/installment/',
			'url'   => home_url( '/installment/' ),
		),
	);

	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-section cttel-v2-mosaic">
		<div class="cttel-container">
			<p class="cttel-v2-eyebrow">دسته‌بندی</p>
			<h2 class="cttel-v2-heading">کشف محصولات CTTEL</h2>
			<p class="cttel-v2-lead">از موبایل و پرچمدار تا جانبی و خدمات اقساطی — با چیدمان ویرایشی برای دسترسی سریع‌تر.</p>
			<div class="cttel-v2-mosaic__grid">
				<?php foreach ( $tiles as $tile ) : ?>
					<?php
					$url = ! empty( $tile['url'] )
						? $tile['url']
						: cttel_home_cat_url( $tile['slug'], $tile['path'] );
					$thumb = '';
					if ( ! empty( $tile['slug'] ) ) {
						$term = get_term_by( 'slug', $tile['slug'], 'product_cat' );
						if ( $term instanceof WP_Term ) {
							$thumb_id = (int) get_term_meta( $term->term_id, 'thumbnail_id', true );
							if ( $thumb_id > 0 ) {
								$thumb = wp_get_attachment_image(
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
					?>
					<a class="cttel-v2-tile cttel-v2-mosaic__tile cttel-v2-mosaic__tile--<?php echo esc_attr( $tile['size'] ); ?>" href="<?php echo esc_url( $url ); ?>">
						<div class="cttel-v2-mosaic__visual">
							<?php
							if ( $thumb ) {
								echo $thumb; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
							} else {
								echo '<span class="cttel-v2-mosaic__placeholder" aria-hidden="true"></span>';
							}
							?>
						</div>
						<div class="cttel-v2-mosaic__copy">
							<h3 class="cttel-v2-mosaic__title"><?php echo esc_html( $tile['title'] ); ?></h3>
							<p class="cttel-v2-mosaic__desc"><?php echo esc_html( $tile['desc'] ); ?></p>
						</div>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_category_mosaic', 'cttel_shortcode_category_mosaic' );

/** Accessory collection editorial tiles (links only — no invented SKUs). */
function cttel_shortcode_accessory_collections(): string {
	$collections = array(
		array( 'title' => 'لوازم آیفون', 'desc' => 'جانبی سازگار با اکوسیستم Apple', 'slug' => 'accessories' ),
		array( 'title' => 'صدا و هندزفری', 'desc' => 'هدفون، ایرباد و hands-free', 'slug' => 'headphones' ),
		array( 'title' => 'شارژ و پاور', 'desc' => 'شارژر، کابل و power bank', 'slug' => 'accessories' ),
		array( 'title' => 'محافظت و کاور', 'desc' => 'گلس، قاب و محافظ بدنه', 'slug' => 'accessories' ),
		array( 'title' => 'ساعت و گجت', 'desc' => 'ساعت هوشمند و گجت', 'slug' => 'gadgets' ),
	);

	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-section cttel-v2-accessories">
		<div class="cttel-container">
			<p class="cttel-v2-eyebrow">لوازم جانبی</p>
			<h2 class="cttel-v2-heading">کلکسیون‌های جانبی</h2>
			<p class="cttel-v2-lead">مسیرهای منتخب برای خرید جانبی — بدون شلوغی ویترین عمومی.</p>
			<div class="cttel-v2-accessories__scroll">
				<?php foreach ( $collections as $col ) : ?>
					<a class="cttel-v2-accessories__card cttel-v2-tile" href="<?php echo esc_url( cttel_home_cat_url( $col['slug'], '/shop/' ) ); ?>">
						<span class="cttel-v2-accessories__index" aria-hidden="true"></span>
						<h3 class="cttel-v2-accessories__title"><?php echo esc_html( $col['title'] ); ?></h3>
						<p class="cttel-v2-accessories__desc"><?php echo esc_html( $col['desc'] ); ?></p>
						<span class="cttel-v2-link-arrow"><?php esc_html_e( 'مشاهده', 'cttel-store' ); ?></span>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_accessory_collections', 'cttel_shortcode_accessory_collections' );

/** Used phone dual-path experience block. */
function cttel_shortcode_used_phone_experience(): string {
	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-section cttel-v2-used">
		<div class="cttel-container cttel-v2-used__grid">
			<div class="cttel-v2-used__intro">
				<p class="cttel-v2-eyebrow">گوشی کارکرده</p>
				<h2 class="cttel-v2-heading">تجربه‌ای متفاوت از بازار کارکرده</h2>
				<p class="cttel-v2-lead">موجودی آماده یا جست‌وجوی اختصاصی — هر دو با استاندارد CTTEL در شفافیت و پیگیری.</p>
			</div>
			<div class="cttel-v2-used__paths">
				<a class="cttel-v2-used__path cttel-v2-tile" href="<?php echo esc_url( home_url( '/used-phone/' ) ); ?>">
					<span class="cttel-v2-used__path-tag"><?php esc_html_e( 'مسیر A', 'cttel-store' ); ?></span>
					<h3 class="cttel-v2-used__path-title">موجودی گوشی‌های کارکرده</h3>
					<p class="cttel-v2-used__path-desc">مشاهده مدل‌های موجود در فروشگاه و خرید مستقیم.</p>
					<span class="cttel-v2-btn cttel-v2-btn--ghost"><?php esc_html_e( 'مشاهده موجودی', 'cttel-store' ); ?></span>
				</a>
				<a class="cttel-v2-used__path cttel-v2-used__path--accent cttel-v2-tile" href="<?php echo esc_url( home_url( '/used-phone-request/' ) ); ?>">
					<span class="cttel-v2-used__path-tag"><?php esc_html_e( 'مسیر B', 'cttel-store' ); ?></span>
					<h3 class="cttel-v2-used__path-title">گوشی موردنظرت رو برات پیدا می‌کنیم</h3>
					<p class="cttel-v2-used__path-desc">ثبت درخواست تأمین با بیعانه — بدون تغییر در فرآیند فعلی سایت.</p>
					<span class="cttel-v2-btn cttel-v2-btn--primary"><?php esc_html_e( 'ثبت درخواست', 'cttel-store' ); ?></span>
				</a>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_used_phone_experience', 'cttel_shortcode_used_phone_experience' );

/** Full-width installment campaign. */
function cttel_shortcode_installment_campaign(): string {
	ob_start();
	?>
	<section class="cttel-v2 cttel-v2-installment-campaign" aria-labelledby="cttel-installment-campaign-title">
		<div class="cttel-v2-installment-campaign__inner">
			<div class="cttel-container cttel-v2-installment-campaign__content">
				<p class="cttel-v2-eyebrow cttel-v2-eyebrow--on-dark"><?php esc_html_e( 'خرید اقساطی', 'cttel-store' ); ?></p>
				<h2 id="cttel-installment-campaign-title" class="cttel-v2-installment-campaign__title">خرید اقساطی با هویت CTTEL</h2>
				<p class="cttel-v2-installment-campaign__lead">محصول را انتخاب کنید و از مسیر اختصاصی اقساط در فروشگاه استفاده کنید — بدون شلوغی اطلاعات غیرضروری در صفحه اصلی.</p>
				<a class="cttel-v2-btn cttel-v2-btn--on-dark" href="<?php echo esc_url( home_url( '/installment/' ) ); ?>"><?php esc_html_e( 'مشاهده خرید اقساطی', 'cttel-store' ); ?></a>
			</div>
			<div class="cttel-v2-installment-campaign__visual" aria-hidden="true"></div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'cttel_installment_campaign', 'cttel_shortcode_installment_campaign' );

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! is_front_page() ) {
			return;
		}
		$path = __DIR__ . '/cttel-home-v2.css';
		if ( ! file_exists( $path ) ) {
			return;
		}
		wp_register_style( 'cttel-home-v2', false, array( 'cttel-design-system' ), '2.0.0' );
		wp_enqueue_style( 'cttel-home-v2' );
		wp_add_inline_style( 'cttel-home-v2', (string) file_get_contents( $path ) );
	},
	25
);
