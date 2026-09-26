#!/usr/bin/env bash
# READ-ONLY production WooCommerce audit via SSH + docker exec wp_app. Never writes.
set -euo pipefail

HOST="${PRODUCTION_SSH_HOST:-${STAGING_SSH_HOST:-root@185.18.214.66}}"
PORT="${PRODUCTION_SSH_PORT:-${STAGING_SSH_PORT:-22}}"
CONTAINER="${PRODUCTION_WP_CONTAINER:-wp_app}"

if [[ "${CONTAINER}" != "wp_app" ]]; then
	echo "Refusing: PRODUCTION_WP_CONTAINER must be wp_app (got ${CONTAINER})"
	exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 -p "${PORT}")
if [[ -n "${STAGING_SSH_PRIVATE_KEY:-}" ]]; then
	KEY_FILE="$(mktemp)"
	printf '%s\n' "${STAGING_SSH_PRIVATE_KEY}" > "${KEY_FILE}"
	chmod 600 "${KEY_FILE}"
	SSH=(ssh -i "${KEY_FILE}" "${SSH_OPTS[@]}")
elif [[ -n "${VPS_PASSWORD:-}" ]]; then
	SSH=(sshpass -p "${VPS_PASSWORD}" ssh "${SSH_OPTS[@]}")
else
	echo "Missing VPS_PASSWORD or STAGING_SSH_PRIVATE_KEY"
	exit 1
fi

REMOTE='docker exec '"${CONTAINER}"' wp --allow-root --path=/var/www/html'

echo "==> PRODUCTION READ-ONLY AUDIT (${CONTAINER} on ${HOST})"
"${SSH[@]}" "${HOST}" "docker ps --format '{{.Names}}' | grep -qx '${CONTAINER}'" || {
	echo "Production container ${CONTAINER} not found"
	exit 1
}

run_ro() {
	"${SSH[@]}" "${HOST}" "${REMOTE} $*"
}

echo "--- CORE ---"
run_ro core version
run_ro plugin get woocommerce --field=version
run_ro eval 'echo PHP_VERSION;'
run_ro theme list --status=active --field=name
run_ro plugin list --status=active --format=csv

echo "--- OPTIONS (checkout/tax/coupons) ---"
for opt in woocommerce_enable_guest_checkout woocommerce_enable_checkout_login_reminder woocommerce_enable_signup_and_login_from_checkout woocommerce_enable_myaccount_registration woocommerce_ship_to_destination woocommerce_calc_taxes woocommerce_enable_coupons; do
	run_ro option get "$opt" 2>/dev/null || echo "${opt}=?"
done

echo "--- PAYMENT GATEWAYS (runtime) ---"
run_ro wc payment_gateway list --format=json 2>/dev/null || run_ro eval-file /dev/stdin <<'PHPEOF'
<?php
if ( ! function_exists( 'WC' ) ) { echo json_encode( array( 'error' => 'no_wc' ) ); return; }
$gws = WC()->payment_gateways()->payment_gateways();
$out = array();
foreach ( $gws as $id => $gw ) {
	$settings = method_exists( $gw, 'get_option' ) ? array() : array();
	if ( method_exists( $gw, 'get_option' ) ) {
		$keys = array( 'enabled', 'title', 'description' );
		foreach ( $keys as $k ) {
			$settings[ $k ] = $gw->get_option( $k );
		}
	}
	$secrets = false;
	if ( is_array( $gw->settings ?? null ) ) {
		foreach ( $gw->settings as $k => $v ) {
			if ( ! is_string( $v ) || '' === trim( $v ) ) {
				continue;
			}
			$kl = strtolower( (string) $k );
			if ( preg_match( '/merchant|api_key|apikey|terminal|password|secret|pin|username|salt/', $kl ) ) {
				$secrets = true;
				break;
			}
		}
	}
	$out[] = array(
		'id' => $id,
		'class' => is_object( $gw ) ? get_class( $gw ) : '',
		'enabled' => $gw->enabled ?? 'no',
		'title' => method_exists( $gw, 'get_title' ) ? $gw->get_title() : '',
		'available' => method_exists( $gw, 'is_available' ) ? ( $gw->is_available() ? 'yes' : 'no' ) : 'unknown',
		'credentials_present' => $secrets ? 'yes' : 'no',
	);
}
echo wp_json_encode( $out, JSON_UNESCAPED_UNICODE );
PHPEOF

echo "--- SHIPPING ZONES ---"
run_ro eval-file /dev/stdin <<'PHPEOF'
<?php
if ( ! class_exists( 'WC_Shipping_Zones' ) ) {
	echo json_encode( array( 'error' => 'no_shipping' ) );
	return;
}
$audit = array();
foreach ( WC_Shipping_Zones::get_zones() as $zone ) {
	$row = array(
		'name' => $zone['zone_name'] ?? '',
		'order' => $zone['zone_order'] ?? 0,
		'locations' => array(),
		'methods' => array(),
	);
	$z = WC_Shipping_Zones::get_zone( $zone['zone_id'] ?? 0 );
	if ( $z ) {
		foreach ( $z->get_zone_locations() as $loc ) {
			$row['locations'][] = array( 'code' => $loc->code ?? '', 'type' => $loc->type ?? '' );
		}
		foreach ( $z->get_shipping_methods( true ) as $m ) {
			$row['methods'][] = array(
				'id' => $m->id ?? '',
				'instance_id' => $m->instance_id ?? null,
				'enabled' => $m->enabled ?? 'no',
				'title' => method_exists( $m, 'get_title' ) ? $m->get_title() : '',
				'cost' => ( 'flat_rate' === ( $m->id ?? '' ) && method_exists( $m, 'get_option' ) ) ? $m->get_option( 'cost', '' ) : null,
			);
		}
	}
	$audit[] = $row;
}
$rest = WC_Shipping_Zones::get_zone( 0 );
if ( $rest ) {
	$row = array( 'name' => 'locations_not_covered', 'locations' => array(), 'methods' => array() );
	foreach ( $rest->get_shipping_methods( true ) as $m ) {
		$row['methods'][] = array(
			'id' => $m->id ?? '',
			'instance_id' => $m->instance_id ?? null,
			'enabled' => $m->enabled ?? 'no',
			'title' => method_exists( $m, 'get_title' ) ? $m->get_title() : '',
			'cost' => ( 'flat_rate' === ( $m->id ?? '' ) && method_exists( $m, 'get_option' ) ) ? $m->get_option( 'cost', '' ) : null,
		);
	}
	$audit[] = $row;
}
echo wp_json_encode( $audit, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
PHPEOF

echo "--- CHECKOUT FIELDS (IR locale) ---"
run_ro eval-file /dev/stdin <<'PHPEOF'
<?php
$fields = WC()->countries->get_address_fields( 'IR', 'billing_' );
$out = array();
foreach ( $fields as $key => $f ) {
	$out[] = array(
		'field' => $key,
		'label' => $f['label'] ?? '',
		'required' => ! empty( $f['required'] ),
	);
}
echo wp_json_encode( $out, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
PHPEOF

echo "--- HEALTH (recent wc/fatal snippets, no PII) ---"
"${SSH[@]}" "${HOST}" "docker exec ${CONTAINER} sh -c 'tail -n 80 /var/www/html/wp-content/debug.log 2>/dev/null | grep -Ei \"fatal|woocommerce|payment|gateway\" | tail -n 20 || echo \"(no debug.log lines or file absent)\"'"

echo "==> AUDIT COMPLETE (read-only)"
