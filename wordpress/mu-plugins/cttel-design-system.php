<?php
/**
 * CTTEL Design System v2 — tokens and global storefront visual layer.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

/** Design tokens as CSS custom properties. */
function cttel_design_system_css(): string {
	return <<<'CSS'
:root {
	--cttel-brand-primary: #1a56db;
	--cttel-brand-primary-hover: #1446b8;
	--cttel-brand-accent: #0ea5e9;
	--cttel-bg: #f4f6f9;
	--cttel-bg-elevated: #eef1f6;
	--cttel-surface: #ffffff;
	--cttel-surface-dark: #0f1419;
	--cttel-surface-dark-soft: #1a222c;
	--cttel-text: #141c26;
	--cttel-text-secondary: #5c6b7a;
	--cttel-text-on-dark: #f3f6fa;
	--cttel-text-muted-on-dark: #a8b4c2;
	--cttel-border: rgba(20, 28, 38, 0.1);
	--cttel-border-strong: rgba(20, 28, 38, 0.16);
	--cttel-success: #0d9488;
	--cttel-warning: #d97706;
	--cttel-radius-sm: 6px;
	--cttel-radius-md: 10px;
	--cttel-radius-lg: 16px;
	--cttel-radius-pill: 999px;
	--cttel-shadow-sm: 0 1px 2px rgba(15, 20, 25, 0.06);
	--cttel-shadow-md: 0 8px 24px rgba(15, 20, 25, 0.08);
	--cttel-shadow-lg: 0 20px 48px rgba(15, 20, 25, 0.12);
	--cttel-container: min(1200px, 92vw);
	--cttel-section-y: clamp(2.5rem, 5vw, 4.5rem);
	--cttel-section-y-tight: clamp(1.75rem, 3vw, 2.75rem);
	--cttel-font-display: clamp(1.75rem, 4.2vw, 3rem);
	--cttel-font-h2: clamp(1.35rem, 2.4vw, 1.75rem);
	--cttel-font-h3: clamp(1.05rem, 1.8vw, 1.25rem);
	--cttel-font-body: 1rem;
	--cttel-font-small: 0.875rem;
	--cttel-font-caption: 0.8125rem;
	--cttel-line-tight: 1.25;
	--cttel-line-body: 1.7;
	--cttel-ease: cubic-bezier(0.22, 1, 0.36, 1);
	--cttel-img-product: 1 / 1;
	--cttel-img-hero: 4 / 3;
}

body.cttel-v2-home,
.cttel-v2 {
	color: var(--cttel-text);
}

.cttel-v2 .cttel-container {
	width: var(--cttel-container);
	margin-inline: auto;
	padding-inline: clamp(1rem, 3vw, 1.5rem);
}

.cttel-v2-section {
	padding-block: var(--cttel-section-y);
}

.cttel-v2-section--tight {
	padding-block: var(--cttel-section-y-tight);
}

.cttel-v2-eyebrow {
	font-size: var(--cttel-font-caption);
	font-weight: 600;
	letter-spacing: 0.04em;
	text-transform: uppercase;
	color: var(--cttel-brand-accent);
	margin: 0 0 0.5rem;
}

.cttel-v2-heading {
	font-size: var(--cttel-font-h2);
	line-height: var(--cttel-line-tight);
	font-weight: 800;
	margin: 0 0 0.65rem;
	color: var(--cttel-text);
}

.cttel-v2-lead {
	font-size: var(--cttel-font-body);
	line-height: var(--cttel-line-body);
	color: var(--cttel-text-secondary);
	margin: 0 0 1.25rem;
	max-width: 42em;
}

.cttel-v2-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.35rem;
	min-height: 44px;
	padding: 0.65rem 1.25rem;
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
	box-shadow: var(--cttel-shadow-md);
}

.cttel-v2-btn--ghost {
	background: transparent;
	color: var(--cttel-text);
	border-color: var(--cttel-border-strong);
}

.cttel-v2-btn--ghost:hover {
	border-color: var(--cttel-brand-primary);
	color: var(--cttel-brand-primary);
}

.cttel-v2-btn--on-dark {
	background: #fff;
	color: var(--cttel-surface-dark);
}

.cttel-v2-link-arrow::before {
	content: "←";
	margin-inline-end: 0.35rem;
	opacity: 0.7;
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
		wp_register_style( 'cttel-design-system', false, array(), '2.0.0' );
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
