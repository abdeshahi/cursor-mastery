<?php
/**
 * Mobile shell — header, bottom nav, assets.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( cttel_mobile_storefront_uses_shell() ) {
			$classes[] = 'cttel-mobile-storefront';
		}
		if ( is_front_page() && ! is_home() ) {
			$classes[] = 'cttel-ms-home';
		}
		if ( cttel_mobile_storefront_is_categories_hub() ) {
			$classes[] = 'cttel-ms-categories';
		}
		return $classes;
	}
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		$css_path = __DIR__ . '/cttel-mobile-storefront.css';
		wp_register_style(
			'cttel-mobile-storefront',
			false,
			array( 'cttel-design-system' ),
			CTTEL_MOBILE_STOREFRONT_VERSION
		);
		wp_enqueue_style( 'cttel-mobile-storefront' );
		if ( is_readable( $css_path ) ) {
			wp_add_inline_style( 'cttel-mobile-storefront', (string) file_get_contents( $css_path ) );
		}

		if ( cttel_mobile_storefront_is_categories_hub() ) {
			wp_register_script(
				'cttel-mobile-storefront-categories',
				false,
				array(),
				CTTEL_MOBILE_STOREFRONT_VERSION,
				true
			);
			wp_enqueue_script( 'cttel-mobile-storefront-categories' );
			wp_add_inline_script(
				'cttel-mobile-storefront-categories',
				cttel_mobile_storefront_categories_js()
			);
		}
	},
	35
);

/** Dequeue legacy homepage / polish styles when mobile storefront is active. */
add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( ! cttel_mobile_storefront_uses_shell() && ! ( is_front_page() && ! is_home() ) ) {
			return;
		}
		wp_dequeue_style( 'cttel-homepage' );
		wp_dequeue_style( 'cttel-home-v2' );
		if ( is_front_page() ) {
			wp_dequeue_style( 'cttel-storefront-polish' );
		}
	},
	120
);

add_action(
	'wp_body_open',
	static function (): void {
		if ( ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		cttel_mobile_storefront_render_header();
	},
	5
);

add_action(
	'wp_footer',
	static function (): void {
		if ( ! cttel_mobile_storefront_uses_shell() ) {
			return;
		}
		cttel_mobile_storefront_render_bottom_nav();
	},
	5
);

/**
 * Cart item count for header badge.
 */
function cttel_mobile_storefront_cart_count(): int {
	if ( ! function_exists( 'WC' ) || ! WC()->cart ) {
		return 0;
	}
	return (int) WC()->cart->get_cart_contents_count();
}

function cttel_mobile_storefront_cart_url(): string {
	return function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );
}

function cttel_mobile_storefront_account_url(): string {
	return function_exists( 'wc_get_page_permalink' )
		? wc_get_page_permalink( 'myaccount' )
		: home_url( '/my-account/' );
}

function cttel_mobile_storefront_home_url(): string {
	return home_url( '/' );
}

function cttel_mobile_storefront_logo_html(): string {
	$custom_logo_id = (int) get_theme_mod( 'custom_logo', 0 );
	if ( $custom_logo_id > 0 ) {
		$img = wp_get_attachment_image(
			$custom_logo_id,
			'medium',
			false,
			array(
				'class'   => 'cttel-ms-header__logo-img',
				'loading' => 'eager',
				'alt'     => get_bloginfo( 'name', 'display' ),
			)
		);
		if ( $img ) {
			return $img;
		}
	}
	return '<span class="cttel-ms-header__logo-text">' . esc_html( get_bloginfo( 'name', 'display' ) ) . '</span>';
}

function cttel_mobile_storefront_render_header(): void {
	$show_search = is_front_page() && ! is_home();
	$cart_count  = cttel_mobile_storefront_cart_count();
	?>
	<header class="cttel-ms-header" role="banner">
		<div class="cttel-ms-header__bar">
			<a class="cttel-ms-header__cart" href="<?php echo esc_url( cttel_mobile_storefront_cart_url() ); ?>" aria-label="<?php esc_attr_e( 'سبد خرید', 'cttel-store' ); ?>">
				<?php echo cttel_mobile_storefront_icon( 'cart' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				<?php if ( $cart_count > 0 ) : ?>
					<span class="cttel-ms-header__cart-count"><?php echo esc_html( (string) $cart_count ); ?></span>
				<?php endif; ?>
			</a>
			<a class="cttel-ms-header__brand" href="<?php echo esc_url( cttel_mobile_storefront_home_url() ); ?>">
				<?php echo cttel_mobile_storefront_logo_html(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
			</a>
		</div>
		<?php if ( $show_search ) : ?>
			<div class="cttel-ms-header__search">
				<?php cttel_mobile_storefront_product_search_form(); ?>
			</div>
		<?php endif; ?>
	</header>
	<?php
}

function cttel_mobile_storefront_product_search_form(): void {
	if ( function_exists( 'woocommerce_product_search_form' ) ) {
		woocommerce_product_search_form();
		return;
	}
	?>
	<form role="search" method="get" class="cttel-ms-search" action="<?php echo esc_url( home_url( '/' ) ); ?>">
		<label class="screen-reader-text" for="cttel-ms-search-field"><?php esc_html_e( 'جستجو', 'cttel-store' ); ?></label>
		<input type="search" id="cttel-ms-search-field" class="cttel-ms-search__input" placeholder="<?php esc_attr_e( 'جستجو', 'cttel-store' ); ?>" value="<?php echo esc_attr( get_search_query() ); ?>" name="s" />
		<input type="hidden" name="post_type" value="product" />
		<button type="submit" class="cttel-ms-search__btn" aria-label="<?php esc_attr_e( 'جستجو', 'cttel-store' ); ?>">
			<?php echo cttel_mobile_storefront_icon( 'search' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
		</button>
	</form>
	<?php
}

/**
 * @param 'home'|'categories'|'account' $active Nav active item.
 */
function cttel_mobile_storefront_render_bottom_nav( string $active = '' ): void {
	if ( '' === $active ) {
		if ( cttel_mobile_storefront_is_categories_hub() ) {
			$active = 'categories';
		} elseif ( is_front_page() && ! is_home() ) {
			$active = 'home';
		} elseif ( function_exists( 'is_account_page' ) && is_account_page() ) {
			$active = 'account';
		}
	}

	$items = array(
		'home'       => array(
			'label' => 'صفحه اصلی',
			'url'   => cttel_mobile_storefront_home_url(),
			'icon'  => 'home',
		),
		'categories' => array(
			'label' => 'دسته‌بندی',
			'url'   => cttel_mobile_storefront_categories_url(),
			'icon'  => 'grid',
		),
		'account'    => array(
			'label' => 'حساب کاربری',
			'url'   => cttel_mobile_storefront_account_url(),
			'icon'  => 'user',
		),
	);
	?>
	<nav class="cttel-ms-bottom-nav" aria-label="<?php esc_attr_e( 'ناوبری اصلی', 'cttel-store' ); ?>">
		<?php foreach ( $items as $key => $item ) : ?>
			<a
				class="cttel-ms-bottom-nav__item<?php echo $key === $active ? ' is-active' : ''; ?>"
				href="<?php echo esc_url( $item['url'] ); ?>"
			>
				<span class="cttel-ms-bottom-nav__icon" aria-hidden="true"><?php echo cttel_mobile_storefront_icon( $item['icon'] ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></span>
				<span class="cttel-ms-bottom-nav__label"><?php echo esc_html( $item['label'] ); ?></span>
			</a>
		<?php endforeach; ?>
	</nav>
	<?php
}

/**
 * Inline SVG icons (no external assets).
 *
 * @param string $name Icon key.
 */
function cttel_mobile_storefront_icon( string $name ): string {
	$icons = array(
		'cart'   => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6 5 3H2"/><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/></svg>',
		'search' => '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
		'home'   => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1z"/></svg>',
		'grid'   => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>',
		'user'   => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4 6-4 8-4s6.5 0 8 4"/></svg>',
		'chev'   => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>',
		'mobile' => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>',
		'laptop' => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="5" width="18" height="12" rx="1.5"/><path d="M2 19h20"/></svg>',
		'tablet' => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M11 17h2"/></svg>',
		'watch'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="7" y="6" width="10" height="12" rx="3"/><path d="M9 6V4h6v2M9 18v2h6v-2"/></svg>',
		'parts'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/></svg>',
		'audio'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 14v-4a2 2 0 0 1 2-2h3l4-3v16l-4-3H6a2 2 0 0 1-2-2z"/><path d="M16 9a3 3 0 0 1 0 6"/></svg>',
		'box'    => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3 4 7v10l8 4 8-4V7z"/><path d="m4 7 8 4 8-4M12 11v10"/></svg>',
	);
	return $icons[ $name ] ?? $icons['box'];
}

/** Map product_cat slug to outline icon. */
function cttel_mobile_storefront_category_icon( WP_Term $term ): string {
	$slug = $term->slug;
	$map  = array(
		'mobile'              => 'mobile',
		'mobile-parts'        => 'parts',
		'mobile_parts'        => 'parts',
		'parts'               => 'parts',
		'laptop'              => 'laptop',
		'tablet'              => 'tablet',
		'smartwatch'          => 'watch',
		'watch'               => 'watch',
		'headphones'          => 'audio',
		'accessories'         => 'box',
	);
	$icon = $map[ $slug ] ?? 'box';
	return cttel_mobile_storefront_icon( $icon );
}
