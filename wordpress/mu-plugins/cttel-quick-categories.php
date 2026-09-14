<?php
/**
 * CTTEL Quick Categories — WooCommerce product categories + editable installment card.
 *
 * Shortcode: [cttel_quick_categories]
 * Categories: Products → Categories (name, thumbnail, description, order, URL).
 * Installment card: Appearance → Customize → CTTEL — دسته‌بندی سریع.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Default installment page URL (resolved from published page slug). */
function cttel_installment_default_url(): string {
	$page = get_page_by_path( 'installment' );
	return $page instanceof WP_Post ? get_permalink( $page ) : home_url( '/' );
}

/** Top-level product categories sorted by WooCommerce term order meta. */
function cttel_get_quick_category_terms(): array {
	$terms = get_terms(
		array(
			'taxonomy'   => 'product_cat',
			'hide_empty' => false,
			'parent'     => 0,
		)
	);

	if ( is_wp_error( $terms ) || empty( $terms ) ) {
		return array();
	}

	usort(
		$terms,
		static function ( WP_Term $a, WP_Term $b ): int {
			$order_a = (int) get_term_meta( $a->term_id, 'order', true );
			$order_b = (int) get_term_meta( $b->term_id, 'order', true );

			if ( $order_a === $order_b ) {
				return strcasecmp( $a->name, $b->name );
			}

			return $order_a <=> $order_b;
		}
	);

	return $terms;
}

/** Installment promo card settings from Customizer. */
function cttel_get_installment_card_settings(): array {
	return array(
		'enabled'     => (bool) get_theme_mod( 'cttel_installment_card_enabled', true ),
		'title'       => get_theme_mod( 'cttel_installment_card_title', 'خرید اقساطی' ),
		'description' => get_theme_mod( 'cttel_installment_card_description', '' ),
		'url'         => get_theme_mod( 'cttel_installment_card_url', cttel_installment_default_url() ),
		'image_id'    => absint( get_theme_mod( 'cttel_installment_card_image', 0 ) ),
		'icon'        => get_theme_mod( 'cttel_installment_card_icon', '💳' ),
		'bg'          => get_theme_mod( 'cttel_installment_card_bg', '#eff6ff' ),
	);
}

/** Fallback icon when a category has no WooCommerce thumbnail. */
function cttel_quick_category_fallback_icon(): string {
	return (string) get_theme_mod( 'cttel_quick_cat_fallback_icon', '📦' );
}

/**
 * Render icon or WooCommerce category thumbnail.
 */
function cttel_quick_category_visual( WP_Term $term ): string {
	$thumb_id = (int) get_term_meta( $term->term_id, 'thumbnail_id', true );

	if ( $thumb_id > 0 ) {
		$img = wp_get_attachment_image(
			$thumb_id,
			'woocommerce_thumbnail',
			false,
			array(
				'class'   => 'cttel-quick-cat-thumb',
				'loading' => 'lazy',
				'alt'     => esc_attr( $term->name ),
			)
		);
		if ( $img ) {
			return '<div class="cttel-quick-cat-visual has-text-align-center">' . $img . '</div>';
		}
	}

	$icon = cttel_quick_category_fallback_icon();
	if ( '' === $icon ) {
		return '<div class="cttel-quick-cat-visual cttel-quick-cat-visual--empty" aria-hidden="true"></div>';
	}

	return '<p class="cttel-quick-cat-icon has-text-align-center">' . esc_html( $icon ) . '</p>';
}

/** Render visual for installment card (image or icon from Customizer). */
function cttel_installment_card_visual( array $settings ): string {
	if ( $settings['image_id'] > 0 ) {
		$img = wp_get_attachment_image(
			$settings['image_id'],
			'woocommerce_thumbnail',
			false,
			array(
				'class'   => 'cttel-quick-cat-thumb',
				'loading' => 'lazy',
				'alt'     => esc_attr( $settings['title'] ),
			)
		);
		if ( $img ) {
			return '<div class="cttel-quick-cat-visual has-text-align-center">' . $img . '</div>';
		}
	}

	$icon = trim( (string) $settings['icon'] );
	if ( '' === $icon ) {
		return '<div class="cttel-quick-cat-visual cttel-quick-cat-visual--empty" aria-hidden="true"></div>';
	}

	return '<p class="cttel-quick-cat-icon has-text-align-center">' . esc_html( $icon ) . '</p>';
}

/** Render a WooCommerce category card. */
function cttel_quick_category_card_from_term( WP_Term $term ): string {
	$url = get_term_link( $term );
	if ( is_wp_error( $url ) ) {
		return '';
	}

	$description = trim( wp_strip_all_tags( $term->description ) );
	$subtitle    = '';

	if ( '' !== $description ) {
		$subtitle = sprintf(
			'<p class="has-text-align-center cttel-quick-cat-sub">%s</p>',
			esc_html( wp_trim_words( $description, 8, '…' ) )
		);
	}

	$title = sprintf(
		'<h3 class="wp-block-heading has-text-align-center cttel-quick-cat-title"><a href="%s">%s</a></h3>',
		esc_url( $url ),
		esc_html( $term->name )
	);

	return sprintf(
		'<div class="cttel-quick-cat-card wp-block-group has-border-color has-tertiary-border-color has-background" style="border-width:1px;border-radius:12px;background-color:#ffffff;">%s%s%s</div>',
		cttel_quick_category_visual( $term ),
		$title,
		$subtitle
	);
}

/** Render installment promo card from Customizer settings. */
function cttel_installment_card_markup( array $settings ): string {
	if ( ! $settings['enabled'] || '' === trim( (string) $settings['title'] ) ) {
		return '';
	}

	$subtitle = '';
	if ( '' !== trim( (string) $settings['description'] ) ) {
		$subtitle = sprintf(
			'<p class="has-text-align-center cttel-quick-cat-sub">%s</p>',
			esc_html( wp_trim_words( wp_strip_all_tags( $settings['description'] ), 8, '…' ) )
		);
	}

	$title = sprintf(
		'<h3 class="wp-block-heading has-text-align-center cttel-quick-cat-title"><a href="%s">%s</a></h3>',
		esc_url( $settings['url'] ),
		esc_html( $settings['title'] )
	);

	return sprintf(
		'<div class="cttel-quick-cat-card wp-block-group has-border-color has-tertiary-border-color has-background" style="border-width:1px;border-radius:12px;background-color:%s;">%s%s%s</div>',
		esc_attr( $settings['bg'] ),
		cttel_installment_card_visual( $settings ),
		$title,
		$subtitle
	);
}

/** Minimal layout CSS (grid: 3 desktop / 2 mobile). */
function cttel_quick_categories_inline_css(): string {
	return '.cttel-quick-cats-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;}'
		. '.cttel-quick-cat-card{padding:1rem .75rem;min-width:0;}'
		. '.cttel-quick-cat-visual{display:flex;align-items:center;justify-content:center;min-height:3rem;margin-bottom:.25rem;}'
		. '.cttel-quick-cat-visual--empty{width:3rem;height:3rem;margin:0 auto;border-radius:8px;background:#f1f5f9;}'
		. '.cttel-quick-cat-thumb{width:3rem;height:3rem;object-fit:contain;border-radius:8px;display:block;margin:0 auto;}'
		. '.cttel-quick-cat-icon{font-size:1.75rem;margin:0;line-height:1;}'
		. '.cttel-quick-cat-title{font-size:1rem;margin:.25rem 0 0;line-height:1.35;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;}'
		. '.cttel-quick-cat-sub{font-size:.75rem;line-height:1.4;margin:.35rem 0 0;opacity:.75;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;}'
		. '@media (max-width:781px){.cttel-quick-cats-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;}}';
}

/**
 * Render quick categories grid.
 */
function cttel_render_quick_categories(): string {
	$cards = array();

	foreach ( cttel_get_quick_category_terms() as $term ) {
		$card = cttel_quick_category_card_from_term( $term );
		if ( '' !== $card ) {
			$cards[] = $card;
		}
	}

	$installment = cttel_installment_card_markup( cttel_get_installment_card_settings() );
	if ( '' !== $installment ) {
		$cards[] = $installment;
	}

	if ( empty( $cards ) ) {
		return '';
	}

	$html = '<style>' . cttel_quick_categories_inline_css() . '</style>';
	$html .= '<div class="cttel-quick-cats-grid">';

	foreach ( $cards as $card ) {
		$html .= '<div class="cttel-quick-cat-item">' . $card . '</div>';
	}

	$html .= '</div>';

	return $html;
}

add_shortcode( 'cttel_quick_categories', 'cttel_render_quick_categories' );

/** Customizer: installment card + category fallback icon. */
add_action(
	'customize_register',
	static function ( WP_Customize_Manager $wp_customize ): void {
		$wp_customize->add_section(
			'cttel_quick_categories',
			array(
				'title'       => 'CTTEL — دسته‌بندی سریع',
				'description' => 'کارت‌های دسته از محصولات → دسته‌ها (نام، تصویر، توضیح، ترتیب) خوانده می‌شوند. کارت «اقساطی» را اینجا ویرایش کنید.',
				'priority'    => 26,
			)
		);

		$wp_customize->add_setting(
			'cttel_quick_cat_fallback_icon',
			array(
				'default'           => '📦',
				'sanitize_callback' => 'sanitize_text_field',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_quick_cat_fallback_icon',
			array(
				'label'       => 'آیکن پیش‌فرض (بدون تصویر دسته)',
				'description' => 'وقتی برای دسته تصویر WooCommerce تنظیم نشده باشد.',
				'section'     => 'cttel_quick_categories',
				'type'        => 'text',
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_enabled',
			array(
				'default'           => true,
				'sanitize_callback' => static function ( $v ) {
					return (bool) $v;
				},
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_installment_card_enabled',
			array(
				'label'   => 'نمایش کارت خرید اقساطی',
				'section' => 'cttel_quick_categories',
				'type'    => 'checkbox',
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_title',
			array(
				'default'           => 'خرید اقساطی',
				'sanitize_callback' => 'sanitize_text_field',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_installment_card_title',
			array(
				'label'   => 'عنوان کارت اقساطی',
				'section' => 'cttel_quick_categories',
				'type'    => 'text',
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_description',
			array(
				'default'           => '',
				'sanitize_callback' => 'sanitize_textarea_field',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_installment_card_description',
			array(
				'label'   => 'توضیح کوتاه کارت اقساطی',
				'section' => 'cttel_quick_categories',
				'type'    => 'textarea',
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_url',
			array(
				'default'           => cttel_installment_default_url(),
				'sanitize_callback' => 'esc_url_raw',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_installment_card_url',
			array(
				'label'       => 'لینک کارت اقساطی',
				'description' => 'پیش‌فرض: برگه «خرید اقساطی».',
				'section'     => 'cttel_quick_categories',
				'type'        => 'url',
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_image',
			array(
				'default'           => 0,
				'sanitize_callback' => 'absint',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			new WP_Customize_Media_Control(
				$wp_customize,
				'cttel_installment_card_image',
				array(
					'label'       => 'تصویر کارت اقساطی',
					'description' => 'در صورت انتخاب، به‌جای آیکن emoji نمایش داده می‌شود.',
					'section'     => 'cttel_quick_categories',
					'mime_type'   => 'image',
				)
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_icon',
			array(
				'default'           => '💳',
				'sanitize_callback' => 'sanitize_text_field',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_installment_card_icon',
			array(
				'label'       => 'آیکن کارت اقساطی (بدون تصویر)',
				'section'     => 'cttel_quick_categories',
				'type'        => 'text',
			)
		);

		$wp_customize->add_setting(
			'cttel_installment_card_bg',
			array(
				'default'           => '#eff6ff',
				'sanitize_callback' => 'sanitize_hex_color',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			new WP_Customize_Color_Control(
				$wp_customize,
				'cttel_installment_card_bg',
				array(
					'label'   => 'رنگ پس‌زمینه کارت اقساطی',
					'section' => 'cttel_quick_categories',
				)
			)
		);
	}
);
