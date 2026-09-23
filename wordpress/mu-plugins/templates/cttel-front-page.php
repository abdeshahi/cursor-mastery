<?php
/**
 * Dedicated CTTEL front page — one presentation source.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="cttel-home" class="cttel-home" role="main">
	<?php cttel_homepage_render_all(); ?>
</main>
<?php
get_footer();
