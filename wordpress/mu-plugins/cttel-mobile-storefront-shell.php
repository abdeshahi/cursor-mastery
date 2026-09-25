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
		if ( function_exists( 'cttel_ms_is_product_archive' ) && cttel_ms_is_product_archive() ) {
			$classes[] = 'cttel-ms-archive';
		}
		if ( function_exists( 'cttel_ms_is_single_product' ) && cttel_ms_is_single_product() ) {
			$classes[] = 'cttel-ms-single';
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
		if ( ( function_exists( 'cttel_ms_is_product_archive' ) && cttel_ms_is_product_archive() )
			|| ( function_exists( 'cttel_ms_is_single_product' ) && cttel_ms_is_single_product() ) ) {
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
	$show_search = false;
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
				<span class="cttel-ms-header__brand-mark">CTTEL</span>
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
		<input type="search" id="cttel-ms-search-field" class="cttel-ms-search__input" placeholder="<?php esc_attr_e( 'جستجوی محصول، مدل یا SKU…', 'cttel-store' ); ?>" value="<?php echo esc_attr( get_search_query() ); ?>" name="s" />
		<input type="hidden" name="post_type" value="product" />
		<button type="submit" class="cttel-ms-search__btn" aria-label="<?php esc_attr_e( 'جستجو', 'cttel-store' ); ?>">
			<?php echo cttel_mobile_storefront_icon( 'search', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
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
