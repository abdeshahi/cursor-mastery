<?php
/**
 * CTTEL Design System — approved mockup tokens (v3).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

function cttel_design_system_css(): string {
	return <<<'CSS'
:root {
	--cttel-navy: #0b1f3a;
	--cttel-navy-deep: #071526;
	--cttel-brand-primary: #2563eb;
	--cttel-brand-primary-hover: #1d4ed8;
	--cttel-brand-accent: #3b82f6;
	--cttel-bg: #f5f7fb;
	--cttel-bg-elevated: #eef3fa;
	--cttel-surface: #ffffff;
	--cttel-surface-muted: #f0f4fa;
	--cttel-surface-dark: #0b1f3a;
	--cttel-surface-dark-soft: #122a4a;
	--cttel-installment-bg: #dbeafe;
	--cttel-installment-surface: #eff6ff;
	--cttel-text: #0b1f3a;
	--cttel-text-secondary: #64748b;
	--cttel-text-muted: #94a3b8;
	--cttel-text-on-dark: #f8fafc;
	--cttel-text-muted-on-dark: #cbd5e1;
	--cttel-border: rgba(11, 31, 58, 0.08);
	--cttel-border-strong: rgba(11, 31, 58, 0.14);
	--cttel-success: #0d9488;
	--cttel-warning: #d97706;
	--cttel-radius-sm: 8px;
	--cttel-radius-md: 12px;
	--cttel-radius-lg: 16px;
	--cttel-radius-xl: 20px;
	--cttel-radius-pill: 999px;
	--cttel-shadow-sm: 0 1px 2px rgba(11, 31, 58, 0.05);
	--cttel-shadow-md: 0 8px 24px rgba(11, 31, 58, 0.08);
	--cttel-shadow-lg: 0 16px 40px rgba(11, 31, 58, 0.12);
	--cttel-container: min(1180px, 92vw);
	--cttel-section-y: clamp(1.25rem, 3vw, 2.25rem);
	--cttel-font-display: clamp(1.65rem, 5vw, 2.35rem);
	--cttel-font-h2: clamp(1.15rem, 2.5vw, 1.45rem);
	--cttel-font-h3: clamp(1rem, 2vw, 1.125rem);
	--cttel-font-body: 0.9375rem;
	--cttel-font-small: 0.8125rem;
	--cttel-font-caption: 0.75rem;
	--cttel-line-tight: 1.3;
	--cttel-line-body: 1.65;
	--cttel-ease: cubic-bezier(0.22, 1, 0.36, 1);
	--cttel-img-product: 1 / 1;
}

body.cttel-v2-home,
.cttel-v2 {
	color: var(--cttel-text);
	font-family: Vazirmatn, system-ui, sans-serif;
}

.cttel-v2 .cttel-container {
	width: var(--cttel-container);
	margin-inline: auto;
	padding-inline: clamp(0.85rem, 3vw, 1.25rem);
}

.cttel-v2-section {
	padding-block: var(--cttel-section-y);
}

.cttel-v2-eyebrow {
	font-size: var(--cttel-font-caption);
	font-weight: 600;
	color: var(--cttel-brand-accent);
	margin: 0 0 0.35rem;
}

.cttel-v2-heading {
	font-size: var(--cttel-font-h2);
	line-height: var(--cttel-line-tight);
	font-weight: 800;
	margin: 0;
	color: var(--cttel-text);
}

.cttel-v2-lead {
	font-size: var(--cttel-font-body);
	line-height: var(--cttel-line-body);
	color: var(--cttel-text-secondary);
	margin: 0.35rem 0 0;
}

.cttel-v2-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.35rem;
	min-height: 44px;
	padding: 0.6rem 1.15rem;
	border-radius: var(--cttel-radius-md);
	font-weight: 700;
	font-size: var(--cttel-font-small);
	text-decoration: none;
	transition: transform 0.2s var(--cttel-ease), box-shadow 0.2s var(--cttel-ease), background 0.2s ease;
	border: 1px solid transparent;
	cursor: pointer;
}

.cttel-v2-btn--primary {
	background: var(--cttel-brand-primary);
	color: #fff;
	box-shadow: var(--cttel-shadow-sm);
}

.cttel-v2-btn--primary:hover {
	background: var(--cttel-brand-primary-hover);
	transform: translateY(-1px);
}

.cttel-v2-btn--outline-light {
	background: transparent;
	color: #fff;
	border-color: rgba(255, 255, 255, 0.45);
}

.cttel-v2-btn--outline-light:hover {
	border-color: #fff;
	background: rgba(255, 255, 255, 0.08);
}

.cttel-v2-btn--outline-dark {
	background: transparent;
	color: #fff;
	border-color: rgba(255, 255, 255, 0.55);
}

.cttel-v2-btn--soft {
	background: var(--cttel-installment-surface);
	color: var(--cttel-brand-primary);
	border-color: rgba(37, 99, 235, 0.15);
}

.cttel-v2-btn__chev::before {
	content: "‹";
	margin-inline-end: 0.25rem;
	font-size: 1.1em;
	line-height: 1;
}

.cttel-v2-section-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.75rem;
	margin-bottom: 0.85rem;
}

.cttel-v2-section-head .cttel-v2-link-all {
	font-size: var(--cttel-font-small);
	font-weight: 700;
	color: var(--cttel-brand-primary);
	text-decoration: none;
	white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
	.cttel-v2-btn,
	.cttel-v2-tile,
	.cttel-pcard {
		transition: none !important;
	}
}
CSS;
}

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		wp_enqueue_style(
			'cttel-vazirmatn',
			'https://fonts.bunny.net/css?family=vazirmatn:400,500,600,700,800',
			array(),
			null
		);
		wp_register_style( 'cttel-design-system', false, array( 'cttel-vazirmatn' ), '4.0.0' );
		wp_enqueue_style( 'cttel-design-system' );
		wp_add_inline_style( 'cttel-design-system', cttel_design_system_css() );
	},
	15
);

add_filter(
	'body_class',
	static function ( array $classes ): array {
		if ( is_front_page() ) {
			$classes[] = 'cttel-v2-home';
		}
		return $classes;
	}
);
