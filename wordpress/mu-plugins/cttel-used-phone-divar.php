<?php
/**
 * CTTEL Used Phone fields + Divar publish queue (no storefront changes).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Meta prefix */
const CTTEL_DIVAR_META_PREFIX = '_cttel_divar_';

/** Divar publish statuses */
const CTTEL_DIVAR_STATUSES = array(
	'not_published',
	'pending',
	'published',
	'failed',
	'sold_closed',
);

/** Register product meta for REST (n8n via WooCommerce API). */
function cttel_divar_meta_keys(): array {
	return array(
		'_cttel_used_phone'           => 'string',
		'_cttel_publish_divar'        => 'string',
		'_cttel_divar_city'           => 'string',
		'_cttel_divar_price'          => 'string',
		'_cttel_divar_title'          => 'string',
		'_cttel_divar_condition'      => 'string',
		'_cttel_divar_battery_health' => 'string',
		'_cttel_divar_storage'        => 'string',
		'_cttel_divar_color'          => 'string',
		'_cttel_divar_body_condition' => 'string',
		'_cttel_divar_repair_history' => 'string',
		'_cttel_divar_registered'     => 'string',
		'_cttel_divar_box'            => 'string',
		'_cttel_divar_accessories'    => 'string',
		'_cttel_divar_warranty'       => 'string',
		'_cttel_divar_description'    => 'string',
		'_cttel_divar_category_slug'  => 'string',
		'_cttel_divar_post_id'        => 'string',
		'_cttel_divar_post_token'     => 'string',
		'_cttel_divar_status'         => 'string',
		'_cttel_divar_last_error'     => 'string',
	);
}

add_action(
	'init',
	static function (): void {
		foreach ( cttel_divar_meta_keys() as $key => $type ) {
			register_post_meta(
				'product',
				$key,
				array(
					'type'              => $type,
					'single'            => true,
					'show_in_rest'      => true,
					'auth_callback'     => static function (): bool {
						return current_user_can( 'edit_products' );
					},
					'sanitize_callback' => 'sanitize_text_field',
				)
			);
		}
	},
	21
);

/** Iranian cities for Divar (slug => label). Extend via filter. */
function cttel_divar_city_options(): array {
	$cities = array(
		'tehran'     => 'تهران',
		'karaj'      => 'کرج',
		'isfahan'    => 'اصفهان',
		'shiraz'     => 'شیراز',
		'mashhad'    => 'مشهد',
		'tabriz'     => 'تبریز',
		'ahvaz'      => 'اهواز',
		'qom'        => 'قم',
		'rasht'      => 'رشت',
		'kermanshah' => 'کرمانشاه',
	);
	return apply_filters( 'cttel_divar_city_options', $cities );
}

function cttel_divar_condition_options(): array {
	return array(
		'like_new'  => 'Like New',
		'very_good' => 'Very Good',
		'good'      => 'Good',
		'fair'      => 'Fair',
	);
}

function cttel_divar_repair_options(): array {
	return array(
		'not_repaired' => 'تعمیر نشده',
		'repaired'     => 'تعمیر شده',
		'unknown'      => 'نامشخص',
	);
}

/** Admin product tab. */
add_filter(
	'woocommerce_product_data_tabs',
	static function ( $tabs ) {
		$tabs['cttel_divar'] = array(
			'label'    => 'CTTEL Used Phone / Divar',
			'target'   => 'cttel_divar_product_data',
			'class'    => array(),
			'priority' => 72,
		);
		return $tabs;
	}
);

add_action(
	'woocommerce_product_data_panels',
	static function (): void {
		global $post;
		$product = wc_get_product( $post );
		if ( ! $product ) {
			return;
		}
		$get = static function ( string $key ) use ( $product ): string {
			return (string) $product->get_meta( $key, true );
		};
		$used     = 'yes' === $get( '_cttel_used_phone' );
		$publish  = 'yes' === $get( '_cttel_publish_divar' );
		$status   = $get( '_cttel_divar_status' ) ?: 'not_published';
		$post_tok = $get( '_cttel_divar_post_token' );
		?>
		<div id="cttel_divar_product_data" class="panel woocommerce_options_panel hidden">
			<p class="form-field" style="padding:12px 12px 0;margin:0;">
				<strong><?php esc_html_e( 'انتشار در دیوار', 'cttel-store' ); ?></strong><br>
				<span class="description"><?php esc_html_e( 'فقط برای گوشی دست‌دوم. WooCommerce منبع اصلی است؛ دیوار کانال انتشار.', 'cttel-store' ); ?></span>
			</p>
			<?php
			woocommerce_wp_checkbox(
				array(
					'id'          => '_cttel_used_phone',
					'label'       => __( 'Used Phone', 'cttel-store' ),
					'description' => __( 'محصول گوشی دست‌دوم است.', 'cttel-store' ),
					'value'       => $used ? 'yes' : 'no',
				)
			);
			?>
			<p class="form-field cttel-divar-publish-wrap" <?php echo $used ? '' : 'style="opacity:.5"'; ?>>
				<label for="_cttel_publish_divar"><?php esc_html_e( 'Publish to Divar', 'cttel-store' ); ?></label>
				<input type="checkbox" class="checkbox" name="_cttel_publish_divar" id="_cttel_publish_divar" value="yes" <?php checked( $publish ); ?> <?php disabled( ! $used ); ?> />
				<span class="description"><?php esc_html_e( 'با ذخیره محصول، درخواست انتشار به n8n ارسال می‌شود (اگر webhook تنظیم شده باشد).', 'cttel-store' ); ?></span>
			</p>
			<div class="cttel-divar-fields" <?php echo $used ? '' : 'style="display:none"'; ?>>
				<?php
				woocommerce_wp_select(
					array(
						'id'      => '_cttel_divar_city',
						'label'   => __( 'Divar City', 'cttel-store' ),
						'options' => array_merge( array( '' => '— انتخاب شهر —' ), cttel_divar_city_options() ),
						'value'   => $get( '_cttel_divar_city' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'          => '_cttel_divar_category_slug',
						'label'       => __( 'Divar category slug', 'cttel-store' ),
						'description' => __( 'اسلاگ دسته دیوار (از پنل کنار / JSON schema). مثال: mobile-phones', 'cttel-store' ),
						'desc_tip'    => true,
						'value'       => $get( '_cttel_divar_category_slug' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'          => '_cttel_divar_price',
						'label'       => __( 'Divar Price', 'cttel-store' ),
						'description' => __( 'خالی = قیمت WooCommerce (تومان)', 'cttel-store' ),
						'desc_tip'    => true,
						'type'        => 'text',
						'value'       => $get( '_cttel_divar_price' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'          => '_cttel_divar_title',
						'label'       => __( 'Divar Title', 'cttel-store' ),
						'description' => __( 'خالی = نام محصول', 'cttel-store' ),
						'desc_tip'    => true,
						'value'       => $get( '_cttel_divar_title' ),
					)
				);
				woocommerce_wp_select(
					array(
						'id'      => '_cttel_divar_condition',
						'label'   => __( 'Condition', 'cttel-store' ),
						'options' => array_merge( array( '' => '—' ), cttel_divar_condition_options() ),
						'value'   => $get( '_cttel_divar_condition' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'    => '_cttel_divar_battery_health',
						'label' => __( 'Battery Health (%)', 'cttel-store' ),
						'type'  => 'number',
						'custom_attributes' => array( 'min' => '0', 'max' => '100', 'step' => '1' ),
						'value' => $get( '_cttel_divar_battery_health' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'    => '_cttel_divar_storage',
						'label' => __( 'Storage', 'cttel-store' ),
						'value' => $get( '_cttel_divar_storage' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'    => '_cttel_divar_color',
						'label' => __( 'Color', 'cttel-store' ),
						'value' => $get( '_cttel_divar_color' ),
					)
				);
				woocommerce_wp_textarea_input(
					array(
						'id'    => '_cttel_divar_body_condition',
						'label' => __( 'Body Condition', 'cttel-store' ),
						'value' => $get( '_cttel_divar_body_condition' ),
					)
				);
				woocommerce_wp_select(
					array(
						'id'      => '_cttel_divar_repair_history',
						'label'   => __( 'Repair History', 'cttel-store' ),
						'options' => array_merge( array( '' => '—' ), cttel_divar_repair_options() ),
						'value'   => $get( '_cttel_divar_repair_history' ),
					)
				);
				woocommerce_wp_checkbox(
					array(
						'id'    => '_cttel_divar_registered',
						'label' => __( 'Registered', 'cttel-store' ),
						'value' => 'yes' === $get( '_cttel_divar_registered' ) ? 'yes' : 'no',
					)
				);
				woocommerce_wp_checkbox(
					array(
						'id'    => '_cttel_divar_box',
						'label' => __( 'Box', 'cttel-store' ),
						'value' => 'yes' === $get( '_cttel_divar_box' ) ? 'yes' : 'no',
					)
				);
				woocommerce_wp_textarea_input(
					array(
						'id'    => '_cttel_divar_accessories',
						'label' => __( 'Accessories', 'cttel-store' ),
						'value' => $get( '_cttel_divar_accessories' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'    => '_cttel_divar_warranty',
						'label' => __( 'Warranty / Test period', 'cttel-store' ),
						'value' => $get( '_cttel_divar_warranty' ),
					)
				);
				woocommerce_wp_textarea_input(
					array(
						'id'    => '_cttel_divar_description',
						'label' => __( 'Divar Description', 'cttel-store' ),
						'value' => $get( '_cttel_divar_description' ),
					)
				);
				woocommerce_wp_text_input(
					array(
						'id'                => '_cttel_divar_post_token',
						'label'             => __( 'Divar Post ID / Token', 'cttel-store' ),
						'value'             => $post_tok,
						'custom_attributes' => array( 'readonly' => 'readonly' ),
					)
				);
				woocommerce_wp_select(
					array(
						'id'      => '_cttel_divar_status',
						'label'   => __( 'Divar Status', 'cttel-store' ),
						'options' => array(
							'not_published' => 'Not Published',
							'pending'       => 'Pending',
							'published'     => 'Published',
							'failed'        => 'Failed',
							'sold_closed'   => 'Sold/Closed',
						),
						'value'   => $status,
						'custom_attributes' => array( 'disabled' => 'disabled' ),
					)
				);
				<input type="hidden" name="_cttel_divar_status" value="<?php echo esc_attr( $status ); ?>" />
			</div>
		</div>
		<script>
		(function(){
			const used = document.getElementById('_cttel_used_phone');
			const pub = document.getElementById('_cttel_publish_divar');
			const wrap = document.querySelector('.cttel-divar-fields');
			const pubWrap = document.querySelector('.cttel-divar-publish-wrap');
			if (!used) return;
			function sync(){
				const on = used.checked;
				if (wrap) wrap.style.display = on ? '' : 'none';
				if (pubWrap) pubWrap.style.opacity = on ? '1' : '.5';
				if (pub) { pub.disabled = !on; if (!on) pub.checked = false; }
			}
			used.addEventListener('change', sync);
			sync();
		})();
		</script>
		<?php
	}
);

/** Save meta + trigger n8n webhook when publish requested. */
add_action(
	'woocommerce_process_product_meta',
	static function ( int $post_id ): void {
		$keys_yes_no = array(
			'_cttel_used_phone',
			'_cttel_publish_divar',
			'_cttel_divar_registered',
			'_cttel_divar_box',
		);
		foreach ( $keys_yes_no as $key ) {
			$val = isset( $_POST[ $key ] ) ? 'yes' : 'no'; // phpcs:ignore WordPress.Security.NonceVerification.Missing
			update_post_meta( $post_id, $key, $val );
		}

		$text_keys = array(
			'_cttel_divar_city',
			'_cttel_divar_price',
			'_cttel_divar_title',
			'_cttel_divar_condition',
			'_cttel_divar_battery_health',
			'_cttel_divar_storage',
			'_cttel_divar_color',
			'_cttel_divar_body_condition',
			'_cttel_divar_repair_history',
			'_cttel_divar_accessories',
			'_cttel_divar_warranty',
			'_cttel_divar_description',
			'_cttel_divar_category_slug',
		);
		foreach ( $text_keys as $key ) {
			if ( isset( $_POST[ $key ] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
				update_post_meta( $post_id, $key, sanitize_text_field( wp_unslash( $_POST[ $key ] ) ) );
			}
		}

		if ( isset( $_POST['_cttel_divar_status'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing
			$st = sanitize_text_field( wp_unslash( $_POST['_cttel_divar_status'] ) );
			if ( in_array( $st, CTTEL_DIVAR_STATUSES, true ) ) {
				update_post_meta( $post_id, '_cttel_divar_status', $st );
			}
		}

		$used    = 'yes' === get_post_meta( $post_id, '_cttel_used_phone', true );
		$publish = 'yes' === get_post_meta( $post_id, '_cttel_publish_divar', true );
		if ( ! $used || ! $publish ) {
			return;
		}

		update_post_meta( $post_id, '_cttel_divar_status', 'pending' );

		$webhook = get_option( 'cttel_n8n_divar_webhook_url', '' );
		if ( ! is_string( $webhook ) || '' === trim( $webhook ) ) {
			return;
		}

		wp_remote_post(
			trim( $webhook ),
			array(
				'timeout' => 15,
				'headers' => array( 'Content-Type' => 'application/json' ),
				'body'    => wp_json_encode(
					array(
						'event'      => 'cttel_divar_publish_requested',
						'product_id' => $post_id,
						'sku'        => get_post_meta( $post_id, '_sku', true ),
						'timestamp'  => gmdate( 'c' ),
					)
				),
			)
		);
	},
	30
);

/** Notify n8n when used phone goes out of stock (sold sync). */
add_action(
	'woocommerce_product_set_stock_status',
	static function ( $product_id, $stock_status, $product ) {
		if ( 'outofstock' !== $stock_status ) {
			return;
		}
		if ( 'yes' !== get_post_meta( $product_id, '_cttel_used_phone', true ) ) {
			return;
		}
		$token = get_post_meta( $product_id, '_cttel_divar_post_token', true );
		if ( ! $token ) {
			return;
		}
		$webhook = get_option( 'cttel_n8n_divar_sold_webhook_url', '' );
		if ( ! is_string( $webhook ) || '' === trim( $webhook ) ) {
			return;
		}
		wp_remote_post(
			trim( $webhook ),
			array(
				'timeout' => 15,
				'headers' => array( 'Content-Type' => 'application/json' ),
				'body'    => wp_json_encode(
					array(
						'event'            => 'cttel_used_phone_sold',
						'product_id'       => $product_id,
						'sku'              => $product instanceof WC_Product ? $product->get_sku() : '',
						'divar_post_token' => $token,
					)
				),
			)
		);
	},
	10,
	3
);

/**
 * Build normalized payload for n8n (also via REST filter).
 *
 * @return array<string,mixed>
 */
function cttel_divar_build_payload( WC_Product $product ): array {
	$price = $product->get_meta( '_cttel_divar_price', true );
	if ( '' === (string) $price ) {
		$price = $product->get_regular_price();
	}
	$title = $product->get_meta( '_cttel_divar_title', true );
	if ( '' === (string) $title ) {
		$title = $product->get_name();
	}
	$images = array();
	$thumb  = wp_get_attachment_url( $product->get_image_id() );
	if ( $thumb ) {
		$images[] = $thumb;
	}
	foreach ( $product->get_gallery_image_ids() as $gid ) {
		$url = wp_get_attachment_url( $gid );
		if ( $url ) {
			$images[] = $url;
		}
	}
	return array(
		'product_id'          => $product->get_id(),
		'sku'                 => $product->get_sku(),
		'name'                => $product->get_name(),
		'used_phone'          => 'yes' === $product->get_meta( '_cttel_used_phone', true ),
		'publish_to_divar'    => 'yes' === $product->get_meta( '_cttel_publish_divar', true ),
		'divar_title'         => $title,
		'divar_price'         => $price,
		'divar_city'          => $product->get_meta( '_cttel_divar_city', true ),
		'divar_category_slug' => $product->get_meta( '_cttel_divar_category_slug', true ),
		'condition'           => $product->get_meta( '_cttel_divar_condition', true ),
		'battery_health'      => $product->get_meta( '_cttel_divar_battery_health', true ),
		'storage'             => $product->get_meta( '_cttel_divar_storage', true ),
		'color'               => $product->get_meta( '_cttel_divar_color', true ),
		'body_condition'      => $product->get_meta( '_cttel_divar_body_condition', true ),
		'repair_history'      => $product->get_meta( '_cttel_divar_repair_history', true ),
		'registered'          => $product->get_meta( '_cttel_divar_registered', true ),
		'box'                 => $product->get_meta( '_cttel_divar_box', true ),
		'accessories'         => $product->get_meta( '_cttel_divar_accessories', true ),
		'warranty'            => $product->get_meta( '_cttel_divar_warranty', true ),
		'description'         => $product->get_meta( '_cttel_divar_description', true ),
		'images'              => $images,
		'divar_post_token'    => $product->get_meta( '_cttel_divar_post_token', true ),
		'divar_status'        => $product->get_meta( '_cttel_divar_status', true ) ?: 'not_published',
		'wc_url'              => get_permalink( $product->get_id() ),
	);
}

add_action(
	'rest_api_init',
	static function (): void {
		register_rest_route(
			'cttel/v1',
			'/divar-product/(?P<id>\d+)',
			array(
				'methods'             => 'GET',
				'callback'            => static function ( WP_REST_Request $request ) {
					$product = wc_get_product( (int) $request['id'] );
					if ( ! $product ) {
						return new WP_Error( 'not_found', 'Product not found', array( 'status' => 404 ) );
					}
					return cttel_divar_build_payload( $product );
				},
				'permission_callback' => static function (): bool {
					return current_user_can( 'edit_products' );
				},
			)
		);
	}
);
