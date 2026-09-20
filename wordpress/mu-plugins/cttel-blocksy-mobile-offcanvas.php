<?php
/**
 * Blocksy mobile off-canvas menu — RTL/right drawer fixes only.
 *
 * Overrides conflicting Additional CSS on `.ct-panel` that breaks #offcanvas
 * (partial inset, wrong slide direction, faded inner panel).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/**
 * Flush Blocksy dynamic CSS once after deploy.
 */
add_action(
	'init',
	static function (): void {
		if ( get_option( 'cttel_offcanvas_fix_v2' ) ) {
			return;
		}
		delete_transient( 'blocksy_dynamic_styles_descriptor' );
		update_option( 'cttel_offcanvas_fix_v2', 1, true );
	},
	5
);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		$css = <<<'CSS'
/* --- Full-viewport overlay (undo broad .ct-panel { inset-inline-* } on offcanvas) --- */
#offcanvas.ct-panel {
	inset: var(--admin-bar, 0px) 0 0 0 !important;
	left: 0 !important;
	right: 0 !important;
	width: auto !important;
	max-width: none !important;
	z-index: 999999;
}
body[data-panel*=in] #offcanvas.ct-panel.active {
	background-color: rgba(0, 0, 0, 0.35);
}
#offcanvas.ct-panel.active {
	opacity: 1;
}

/* --- Right-side drawer: closed off-screen to the right --- */
#offcanvas[data-behaviour*=right-side] .ct-panel-inner {
	--theme-panel-reveal-right: 100%;
	right: 0;
	left: auto;
	margin-inline-start: auto;
	margin-inline-end: 0;
	background-color: #121519 !important;
	opacity: 1 !important;
	filter: none !important;
	backdrop-filter: none !important;
	-webkit-backdrop-filter: none !important;
}
#offcanvas[data-behaviour*=right-side]:not(.active) .ct-panel-inner {
	transform: translate3d(100%, 0, 0);
}
[data-panel*=in] #offcanvas[data-behaviour*=right-side].active .ct-panel-inner {
	transform: translate3d(0, 0, 0);
}

/* --- RTL content inside drawer only --- */
#offcanvas,
#offcanvas .ct-panel-content,
#offcanvas .ct-panel-content-inner,
#offcanvas .mobile-menu {
	direction: rtl;
	text-align: right;
}

/* --- Menu rows: touch targets, no overlap --- */
#offcanvas .mobile-menu.menu-container > ul {
	width: 100%;
	margin: 0;
	padding: 0;
	list-style: none;
}
#offcanvas .mobile-menu li {
	width: 100%;
	position: relative;
}
#offcanvas .mobile-menu .ct-menu-link,
#offcanvas .mobile-menu .ct-sub-menu-parent {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	gap: 0.5rem;
	min-height: 44px;
	padding-inline: var(--panel-padding, 25px);
	width: 100%;
	box-sizing: border-box;
	line-height: 1.4;
	white-space: normal;
}
#offcanvas .mobile-menu .ct-toggle-dropdown-mobile {
	min-width: 44px;
	min-height: 44px;
	margin-inline-start: auto;
	margin-inline-end: 0;
	flex-shrink: 0;
}
#offcanvas .mobile-menu .sub-menu {
	position: static !important;
	inset: auto !important;
	width: 100%;
	box-shadow: none;
	opacity: 1 !important;
	filter: none !important;
	background: rgba(255, 255, 255, 0.06);
	margin: 0;
	padding-inline: 0;
}
#offcanvas .mobile-menu .sub-menu .ct-menu-link {
	padding-inline-start: calc(var(--panel-padding, 25px) + 0.75rem);
}

/* --- Close control --- */
#offcanvas .ct-panel-actions {
	flex-shrink: 0;
	z-index: 2;
	padding-bottom: 0.25rem;
}
#offcanvas .ct-panel-actions .ct-toggle-close {
	min-width: 44px;
	min-height: 44px;
}

/* --- Drawer width on small screens --- */
@media (max-width: 999.98px) {
	#offcanvas {
		--side-panel-width: min(86vw, 420px);
	}
}
@media (max-width: 689.98px) {
	#offcanvas {
		--side-panel-width: min(88vw, 400px);
	}
}

#offcanvas .ct-panel-content-inner {
	overflow-x: hidden;
	max-width: 100%;
}

body[data-panel] {
	overflow-x: hidden;
}
CSS;

		wp_register_style( 'cttel-blocksy-offcanvas', false, array(), '2.0.0' );
		wp_enqueue_style( 'cttel-blocksy-offcanvas' );
		wp_add_inline_style( 'cttel-blocksy-offcanvas', $css );
	},
	999
);

/**
 * Stop broad Customizer rule `.ct-panel { inset-inline-* }` from breaking the mobile drawer.
 */
add_filter(
	'wp_get_custom_css',
	static function ( $css ) {
		if ( ! is_string( $css ) || '' === $css ) {
			return $css;
		}
		$css = preg_replace(
			'/(\.header-menu-container \.sub-menu,\s*\.menu \.sub-menu,\s*ul\.dropdown-menu,\s*\.ct-header-account-dropdown,\s*)\.ct-panel\s*\{/',
			'$1.ct-header-account-dropdown {',
			$css
		);
		return $css;
	}
);
