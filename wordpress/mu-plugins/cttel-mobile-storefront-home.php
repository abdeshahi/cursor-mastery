<?php
/**
 * Mobile storefront homepage — sales-first, real WooCommerce inventory only.
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
 * Quick nav targets (catalog slugs).
 *
 * @return array<int, array{slug: string, label: string}>
 */
function cttel_ms_home_quick_nav_items(): array {
	return array(
		array(
			'slug'  => 'mobile-new',
			'label' => __( 'گوشی نو', 'cttel-store' ),
		),
		array(
			'slug'  => 'mobile-used',
			'label' => __( 'گوشی کارکرده', 'cttel-store' ),
		),
		array(
			'slug'  => 'accessories',
			'label' => __( 'لوازم جانبی', 'cttel-store' ),
		),
		array(
			'slug'  => 'gadget',
			'label' => __( 'گجت', 'cttel-store' ),
		),
	);
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
			'featured' => true,
			'orderby'  => 'date',
			'order'    => 'DESC',
		),
		array(
			'limit'    => $limit * 3,
			'status'   => 'publish',
			'on_sale'  => true,
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

/**
 * Products from multiple category slugs (deduped, newest first).
 *
 * @param string[] $slugs
 * @return WC_Product[]
 */
function cttel_ms_home_products_in_categories( array $slugs, int $limit = 8 ): array {
	if ( ! function_exists( 'wc_get_products' ) || empty( $slugs ) ) {
		return array();
	}
	$valid = array();
	foreach ( $slugs as $slug ) {
		$term = get_term_by( 'slug', sanitize_title( $slug ), 'product_cat' );
		if ( $term instanceof WP_Term ) {
			$valid[] = $slug;
		}
	}
	if ( empty( $valid ) ) {
		return array();
	}
	$found = wc_get_products(
		array(
			'limit'    => $limit * 4,
			'status'   => 'publish',
			'category' => $valid,
			'orderby'  => 'date',
			'order'    => 'DESC',
		)
	);
	$seen = array();
	$out  = array();
	foreach ( $found as $product ) {
		if ( ! $product instanceof WC_Product ) {
			continue;
		}
		$id = $product->get_id();
		if ( isset( $seen[ $id ] ) ) {
			continue;
		}
		$seen[ $id ] = true;
		$out[]       = $product;
		if ( count( $out ) >= $limit ) {
			break;
		}
	}
	return $out;
}

/**
 * @return string
 */
function cttel_ms_home_term_url( string $slug ): string {
	$term = get_term_by( 'slug', $slug, 'product_cat' );
	if ( $term instanceof WP_Term ) {
		$link = get_term_link( $term );
		return is_wp_error( $link ) ? '' : (string) $link;
	}
	return '';
}

function cttel_ms_home_render(): void {
	cttel_ms_home_render_hero();
	cttel_ms_home_render_quick_nav();
	cttel_ms_home_render_product_section(
		__( 'لوازم جانبی', 'cttel-store' ),
		'accessories',
		cttel_ms_home_products_in_categories(
			array(
				'acc-case',
				'acc-glass',
				'acc-charger',
				'acc-cable',
				'acc-powerbank',
				'acc-headphone',
				'accessories',
			),
			8
		),
		cttel_ms_home_term_url( 'accessories' ),
		array(
			'view_all_label' => __( 'مشاهده همه لوازم جانبی', 'cttel-store' ),
		)
	);
	cttel_ms_home_render_product_section(
		__( 'گجت‌ها', 'cttel-store' ),
		'gadget',
		function_exists( 'cttel_catalog_products_in_category' ) ? cttel_catalog_products_in_category( 'gadget', 8 ) : array(),
		cttel_ms_home_term_url( 'gadget' ),
		array(
			'view_all_label' => __( 'مشاهده همه گجت‌ها', 'cttel-store' ),
		)
	);
	cttel_ms_home_render_product_section(
		__( 'گوشی‌های کارکرده موجود', 'cttel-store' ),
		'mobile-used',
		function_exists( 'cttel_catalog_products_in_category' ) ? cttel_catalog_products_in_category( 'mobile-used', 8 ) : array(),
		cttel_ms_home_term_url( 'mobile-used' ),
		array(
			'section_class' => 'cttel-ms-home-section--used',
			'intro'         => __( 'هر دستگاه موجودی جداگانه، مشخصات و وضعیت واقعی دارد.', 'cttel-store' ),
			'view_all_label' => __( 'مشاهده همه کارکرده‌ها', 'cttel-store' ),
		)
	);
	cttel_ms_home_render_product_section(
		__( 'گوشی نو — خرید نقدی', 'cttel-store' ),
		'mobile-new',
		function_exists( 'cttel_catalog_products_in_category' ) ? cttel_catalog_products_in_category( 'mobile-new', 8 ) : array(),
		cttel_ms_home_term_url( 'mobile-new' ),
		array(
			'view_all_label' => __( 'مشاهده همه گوشی‌های نو', 'cttel-store' ),
		)
	);
	cttel_ms_home_render_installment();
	cttel_ms_home_render_trust();
}

function cttel_ms_home_render_hero(): void {
	$shop = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );
	$inst = function_exists( 'cttel_installment_default_url' ) ? cttel_installment_default_url() : home_url( '/installment/' );
	?>
	<section class="cttel-ms-hero cttel-ms-hero--compact" aria-labelledby="cttel-ms-hero-title">
		<div class="cttel-ms-hero__card cttel-ms-hero__card--compact">
			<div class="cttel-ms-hero__body">
				<h1 id="cttel-ms-hero-title" class="cttel-ms-hero__title"><?php esc_html_e( 'فروشگاه موبایل، لوازم جانبی و گجت CTTEL', 'cttel-store' ); ?></h1>
				<p class="cttel-ms-hero__lead"><?php esc_html_e( 'خرید آنلاین با موجودی واقعی، قیمت به‌روز و ارسال به سراسر ایران', 'cttel-store' ); ?></p>
				<div class="cttel-ms-hero__search">
					<?php cttel_mobile_storefront_product_search_form(); ?>
				</div>
				<div class="cttel-ms-hero__actions">
					<a class="cttel-ms-btn cttel-ms-btn--primary" href="<?php echo esc_url( $shop ); ?>"><?php esc_html_e( 'مشاهده محصولات', 'cttel-store' ); ?></a>
					<a class="cttel-ms-btn cttel-ms-btn--outline" href="<?php echo esc_url( $inst ); ?>"><?php esc_html_e( 'شرایط خرید اقساطی', 'cttel-store' ); ?></a>
				</div>
			</div>
		</div>
	</section>
	<?php
}

function cttel_ms_home_render_quick_nav(): void {
	$items = cttel_ms_home_quick_nav_items();
	?>
	<section class="cttel-ms-cat-cards" aria-labelledby="cttel-ms-cat-cards-title">
		<h2 id="cttel-ms-cat-cards-title" class="cttel-ms-cat-cards__heading"><?php esc_html_e( 'خرید بر اساس دسته', 'cttel-store' ); ?></h2>
	<nav class="cttel-ms-quick-nav" aria-label="<?php esc_attr_e( 'دسته‌های فروشگاه', 'cttel-store' ); ?>">
		<ul class="cttel-ms-quick-nav__list">
			<?php foreach ( $items as $item ) : ?>
				<?php
				$url = cttel_ms_home_term_url( $item['slug'] );
				if ( '' === $url ) {
					continue;
				}
				$term = get_term_by( 'slug', $item['slug'], 'product_cat' );
				?>
				<li>
					<a class="cttel-ms-quick-nav__item" href="<?php echo esc_url( $url ); ?>">
						<?php if ( $term instanceof WP_Term ) : ?>
							<span class="cttel-ms-quick-nav__icon"><?php echo cttel_mobile_storefront_category_icon( $term ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
						<?php endif; ?>
						<span class="cttel-ms-quick-nav__label"><?php echo esc_html( $item['label'] ); ?></span>
					</a>
				</li>
			<?php endforeach; ?>
		</ul>
	</nav>
	</section>
	<?php
}

/**
 * @param WC_Product[] $products
 * @param array{section_class?: string, intro?: string, view_all_label?: string} $opts
 */
function cttel_ms_home_render_product_section( string $title, ?string $category_slug, array $products, string $view_all_url = '', array $opts = array() ): void {
	$section_id = 'cttel-ms-home-' . sanitize_title( $title );
	$section_cl = 'cttel-ms-home-section';
	if ( ! empty( $opts['section_class'] ) ) {
		$section_cl .= ' ' . sanitize_html_class( (string) $opts['section_class'] );
	}
	$view_label = ! empty( $opts['view_all_label'] ) ? (string) $opts['view_all_label'] : __( 'مشاهده همه', 'cttel-store' );
	?>
	<section class="<?php echo esc_attr( $section_cl ); ?>" aria-labelledby="<?php echo esc_attr( $section_id ); ?>">
		<div class="cttel-ms-section-head">
			<h2 id="<?php echo esc_attr( $section_id ); ?>" class="cttel-ms-section-head__title"><?php echo esc_html( $title ); ?></h2>
			<?php if ( '' !== $view_all_url ) : ?>
				<a class="cttel-ms-section-head__link" href="<?php echo esc_url( $view_all_url ); ?>"><?php echo esc_html( $view_label ); ?></a>
			<?php endif; ?>
		</div>
		<?php if ( ! empty( $opts['intro'] ) ) : ?>
			<p class="cttel-ms-home-section__intro"><?php echo esc_html( (string) $opts['intro'] ); ?></p>
		<?php endif; ?>
		<?php if ( empty( $products ) ) : ?>
			<div class="cttel-ms-empty cttel-ms-empty--section">
				<?php if ( 'mobile-used' === $category_slug ) : ?>
					<p class="cttel-ms-empty__text"><?php esc_html_e( 'فعلاً گوشی کارکرده‌ای در انبار نیست.', 'cttel-store' ); ?></p>
					<?php
					$used_req = function_exists( 'cttel_used_phone_request_url' ) ? cttel_used_phone_request_url() : home_url( '/used-phone-request/' );
					?>
					<a class="cttel-ms-btn cttel-ms-btn--outline cttel-ms-empty__cta" href="<?php echo esc_url( $used_req ); ?>"><?php esc_html_e( 'درخواست گوشی کارکرده', 'cttel-store' ); ?></a>
				<?php else : ?>
					<p class="cttel-ms-empty__text"><?php esc_html_e( 'محصولی برای نمایش در این بخش یافت نشد.', 'cttel-store' ); ?></p>
				<?php endif; ?>
			</div>
		<?php else : ?>
			<?php
			$product_count = count( $products );
			$grid_class    = 'cttel-ms-products__grid';
			if ( 1 === $product_count ) {
				$grid_class .= ' cttel-ms-products__grid--single';
			}
			?>
			<ul class="<?php echo esc_attr( $grid_class ); ?>">
				<?php foreach ( $products as $product ) : ?>
					<?php
					if ( ! $product instanceof WC_Product ) {
						continue;
					}
					echo cttel_ms_product_card( $product, 1 === $product_count ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
					?>
				<?php endforeach; ?>
			</ul>
		<?php endif; ?>
	</section>
	<?php
}

/**
 * @return string
 */
function cttel_ms_product_card( WC_Product $product, bool $solo = false ): string {
	if ( function_exists( 'cttel_ms_render_product_card' ) ) {
		return cttel_ms_render_product_card(
			$product,
			array(
				'variant'   => $solo ? 'solo' : 'grid',
				'show_cta'  => true,
			)
		);
	}
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
	$page_url = function_exists( 'cttel_installment_default_url' ) ? cttel_installment_default_url() : home_url( '/installment/' );
	$lead_url = function_exists( 'cttel_installment_consultation_url' ) ? cttel_installment_consultation_url() : '';
	$lead_lbl = function_exists( 'cttel_installment_consultation_label' ) ? cttel_installment_consultation_label() : __( 'مشاوره خرید اقساطی', 'cttel-store' );
	?>
	<section class="cttel-ms-installment cttel-ms-installment--home" aria-labelledby="cttel-ms-installment-home-title">
		<div class="cttel-ms-installment__inner">
			<h2 id="cttel-ms-installment-home-title" class="cttel-ms-installment__title"><?php esc_html_e( 'خرید اقساطی موبایل و کالا', 'cttel-store' ); ?></h2>
			<p class="cttel-ms-installment__desc"><?php esc_html_e( 'خرید اقساطی CTTEL به‌صورت حضوری و پس از بررسی شرایط انجام می‌شود.', 'cttel-store' ); ?></p>
			<div class="cttel-ms-installment__actions">
				<a class="cttel-ms-btn cttel-ms-btn--outline" href="<?php echo esc_url( $page_url ); ?>"><?php esc_html_e( 'مشاهده شرایط خرید اقساطی', 'cttel-store' ); ?></a>
				<?php if ( '' !== $lead_url ) : ?>
					<a class="cttel-ms-btn cttel-ms-btn--ghost" href="<?php echo esc_url( $lead_url ); ?>"><?php echo esc_html( $lead_lbl ); ?></a>
				<?php endif; ?>
			</div>
		</div>
	</section>
	<?php
}

function cttel_ms_home_render_trust(): void {
	$items = array(
		__( 'پشتیبانی فروشگاه', 'cttel-store' ),
		__( 'ضمانت اصالت کالا', 'cttel-store' ),
		__( 'پرداخت امن آنلاین', 'cttel-store' ),
		__( 'ارسال با تیپاکس یا ماهکس — هزینه ارسال هنگام تحویل توسط مشتری به شرکت حمل پرداخت می‌شود.', 'cttel-store' ),
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
