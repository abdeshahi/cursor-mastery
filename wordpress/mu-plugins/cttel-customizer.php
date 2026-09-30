<?php
/**
 * CTTEL Brand Kit — simplified Customizer panel syncing to Blocksy theme mods.
 *
 * Appearance → Customize → CTTEL — هویت بصری
 * No layout/CSS hard-coding; syncs to native Blocksy settings.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Persian font presets (Google) + local hook for self-hosted fonts. */
function cttel_font_presets(): array {
	return array(
		'vazirmatn'  => array(
			'label'  => 'Vazirmatn',
			'family' => 'Vazirmatn',
			'source' => 'google',
		),
		'sahel'      => array(
			'label'  => 'Sahel',
			'family' => 'Sahel',
			'source' => 'google',
		),
		'shabnam'    => array(
			'label'  => 'Shabnam',
			'family' => 'Shabnam',
			'source' => 'google',
		),
		'iransans'   => array(
			'label'  => 'IRANSansX',
			'family' => 'IRANSansX',
			'source' => 'google',
		),
		'local'      => array(
			'label'  => 'فونت محلی (uploads/cttel-fonts/)',
			'family' => 'CTTELLocal',
			'source' => 'local',
		),
	);
}

/**
 * Build Blocksy typography array.
 *
 * @param string $family Font family.
 * @param string $size   Font size.
 * @param string $weight Variation e.g. n4, n7.
 */
function cttel_typography( string $family, string $size = '16px', string $weight = 'n4' ): array {
	if ( function_exists( 'blocksy_typography_default_values' ) ) {
		return blocksy_typography_default_values(
			array(
				'family'          => $family,
				'variation'       => $weight,
				'size'            => $size,
				'line-height'     => '1.75',
				'letter-spacing'  => '0em',
				'text-transform'  => 'none',
				'text-decoration' => 'none',
			)
		);
	}

	return array(
		'family'    => $family,
		'variation' => $weight,
		'size'      => $size,
	);
}

/** Apply font preset to Blocksy typography mods. */
function cttel_apply_font_preset( string $preset, string $local_name = 'CTTELLocal' ): void {
	$presets = cttel_font_presets();
	if ( ! isset( $presets[ $preset ] ) ) {
		$preset = 'vazirmatn';
	}

	$family = 'local' === $preset ? $local_name : $presets[ $preset ]['family'];

	set_theme_mod( 'rootTypography', cttel_typography( $family, '16px', 'n4' ) );
	set_theme_mod( 'h1Typography', cttel_typography( $family, '36px', 'n7' ) );
	set_theme_mod( 'h2Typography', cttel_typography( $family, '30px', 'n7' ) );
	set_theme_mod( 'h3Typography', cttel_typography( $family, '24px', 'n6' ) );
	set_theme_mod( 'buttonsTypography', cttel_typography( $family, '15px', 'n5' ) );
}

/** Merge a palette color into Blocksy colorPalette mod. */
function cttel_set_palette_color( string $key, string $hex ): void {
	if ( ! function_exists( 'blocksy_manager' ) ) {
		return;
	}

	$palette = get_theme_mod( 'colorPalette' );
	if ( ! is_array( $palette ) || empty( $palette ) ) {
		$palette = blocksy_manager()->colors->get_color_palette();
	}

	if ( isset( $palette[ $key ] ) ) {
		$palette[ $key ]['color'] = $hex;
		set_theme_mod( 'colorPalette', $palette );
	}
}

/** Sync CTTEL Brand Kit settings → Blocksy theme mods. */
function cttel_sync_brand_kit( WP_Customize_Manager $wp_customize ): void {
	$primary   = get_theme_mod( 'cttel_primary_color', '#2872fa' );
	$secondary = get_theme_mod( 'cttel_secondary_color', '#1559ed' );
	$accent    = get_theme_mod( 'cttel_accent_color', '#1e40af' );
	$bg        = get_theme_mod( 'cttel_bg_color', '#FAFBFC' );
	$surface   = get_theme_mod( 'cttel_surface_color', '#ffffff' );
	$text      = get_theme_mod( 'cttel_text_color', '#3A4F66' );
	$btn       = get_theme_mod( 'cttel_button_color', $primary );
	$btn_hover = get_theme_mod( 'cttel_button_hover_color', $secondary );
	$header_bg = get_theme_mod( 'cttel_header_bg_color', '#ffffff' );
	$footer_bg = get_theme_mod( 'cttel_footer_bg_color', '#f2f5f7' );
	$radius    = absint( get_theme_mod( 'cttel_border_radius', 8 ) );

	cttel_set_palette_color( 'color1', $primary );
	cttel_set_palette_color( 'color2', $secondary );
	cttel_set_palette_color( 'color3', $text );
	cttel_set_palette_color( 'color4', '#192a3d' );
	cttel_set_palette_color( 'color6', $footer_bg );
	cttel_set_palette_color( 'color7', $bg );
	cttel_set_palette_color( 'color8', $surface );

	set_theme_mod(
		'fontColor',
		array(
			'default' => array( 'color' => $text ),
		)
	);

	set_theme_mod(
		'buttonColor',
		array(
			'default' => array( 'color' => $btn ),
			'hover'   => array( 'color' => $btn_hover ),
		)
	);

	set_theme_mod(
		'buttonTextColor',
		array(
			'default' => array( 'color' => '#ffffff' ),
			'hover'   => array( 'color' => '#ffffff' ),
		)
	);

	set_theme_mod( 'buttonRadius', $radius );

	set_theme_mod(
		'footerBackground',
		array(
			'default' => array( 'color' => $footer_bg ),
		)
	);

	$preset     = get_theme_mod( 'cttel_font_preset', 'vazirmatn' );
	$local_name = get_theme_mod( 'cttel_local_font_name', 'CTTELLocal' );
	cttel_apply_font_preset( $preset, $local_name );

	// Header row background via placements settings (middle-row).
	$header = get_theme_mod( 'header_placements' );
	if ( is_array( $header ) ) {
		foreach ( $header['sections'] as &$section ) {
			if ( 'type-1' !== ( $section['id'] ?? '' ) ) {
				continue;
			}
			$section['settings']['headerBackground'] = array(
				'default' => array( 'color' => $header_bg ),
			);
		}
		unset( $section );
		set_theme_mod( 'header_placements', $header );
	}

	delete_transient( 'blocksy_dynamic_styles_descriptor' );
}

add_action(
	'customize_register',
	static function ( WP_Customize_Manager $wp_customize ): void {
		$wp_customize->add_panel(
			'cttel_brand',
			array(
				'title'       => 'CTTEL — هویت بصری',
				'description' => 'تنظیمات سریع برند. پس از ذخیره، Blocksy به‌روز می‌شود. جزئیات: General / Header Builder / Footer Builder.',
				'priority'    => 25,
			)
		);

		$wp_customize->add_section(
			'cttel_colors',
			array(
				'title' => 'رنگ‌های برند',
				'panel' => 'cttel_brand',
			)
		);

		$colors = array(
			'cttel_primary_color'       => array( 'رنگ اصلی (Primary)', '#2872fa' ),
			'cttel_secondary_color'     => array( 'رنگ ثانویه', '#1559ed' ),
			'cttel_accent_color'        => array( 'Accent', '#1e40af' ),
			'cttel_bg_color'            => array( 'پس‌زمینه صفحه', '#FAFBFC' ),
			'cttel_surface_color'       => array( 'پس‌زمینه کارت', '#ffffff' ),
			'cttel_text_color'          => array( 'رنگ متن', '#3A4F66' ),
			'cttel_button_color'        => array( 'رنگ دکمه', '#2872fa' ),
			'cttel_button_hover_color'  => array( 'رنگ hover دکمه', '#1559ed' ),
			'cttel_header_bg_color'    => array( 'پس‌زمینه Header', '#ffffff' ),
			'cttel_footer_bg_color'    => array( 'پس‌زمینه Footer', '#f2f5f7' ),
		);

		foreach ( $colors as $id => $meta ) {
			$wp_customize->add_setting(
				$id,
				array(
					'default'           => $meta[1],
					'sanitize_callback' => 'sanitize_hex_color',
					'transport'         => 'refresh',
				)
			);
			$wp_customize->add_control(
				new WP_Customize_Color_Control(
					$wp_customize,
					$id,
					array(
						'label'   => $meta[0],
						'section' => 'cttel_colors',
					)
				)
			);
		}

		$wp_customize->add_setting(
			'cttel_border_radius',
			array(
				'default'           => 8,
				'sanitize_callback' => 'absint',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_border_radius',
			array(
				'label'       => 'Border radius سراسری (px)',
				'section'     => 'cttel_colors',
				'type'        => 'number',
				'input_attrs' => array(
					'min'  => 0,
					'max'  => 32,
					'step' => 1,
				),
			)
		);

		$wp_customize->add_section(
			'cttel_fonts',
			array(
				'title' => 'فونت فارسی',
				'panel' => 'cttel_brand',
			)
		);

		$choices = array();
		foreach ( cttel_font_presets() as $key => $preset ) {
			$choices[ $key ] = $preset['label'];
		}

		$wp_customize->add_setting(
			'cttel_font_preset',
			array(
				'default'           => 'vazirmatn',
				'sanitize_callback' => static function ( $v ) {
					return array_key_exists( $v, cttel_font_presets() ) ? $v : 'vazirmatn';
				},
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_font_preset',
			array(
				'label'   => 'فونت سراسری',
				'section' => 'cttel_fonts',
				'type'    => 'select',
				'choices' => $choices,
			)
		);

		$wp_customize->add_setting(
			'cttel_local_font_name',
			array(
				'default'           => 'CTTELLocal',
				'sanitize_callback' => 'sanitize_text_field',
				'transport'         => 'refresh',
			)
		);
		$wp_customize->add_control(
			'cttel_local_font_name',
			array(
				'label'       => 'نام فونت محلی',
				'description' => 'فایل‌ها را در wp-content/uploads/cttel-fonts/ قرار دهید (woff2).',
				'section'     => 'cttel_fonts',
				'type'        => 'text',
			)
		);
	}
);

add_action(
	'customize_save_after',
	static function ( WP_Customize_Manager $wp_customize ): void {
		cttel_sync_brand_kit( $wp_customize );
	}
);

/** Self-hosted @font-face when local preset is active. */
add_action(
	'wp_enqueue_scripts',
	static function (): void {
		if ( 'local' !== get_theme_mod( 'cttel_font_preset', 'vazirmatn' ) ) {
			return;
		}

		$name = get_theme_mod( 'cttel_local_font_name', 'CTTELLocal' );
		$base = content_url( 'uploads/cttel-fonts/' );
		$css  = "@font-face{font-family:'{$name}';src:url('{$base}{$name}-Regular.woff2') format('woff2');font-weight:400;font-display:swap;}"
			. "@font-face{font-family:'{$name}';src:url('{$base}{$name}-Bold.woff2') format('woff2');font-weight:700;font-display:swap;}";

		wp_register_style( 'cttel-local-font', false );
		wp_enqueue_style( 'cttel-local-font' );
		wp_add_inline_style( 'cttel-local-font', $css );
	},
	99
);

/** Seed defaults on first run. */
add_action(
	'after_setup_theme',
	static function (): void {
		if ( get_option( 'cttel_brand_kit_seeded' ) ) {
			return;
		}
		cttel_apply_font_preset( 'vazirmatn' );
		update_option( 'cttel_brand_kit_seeded', 1 );
	},
	20
);
