<?php
/**
 * CTTEL mobile storefront front page.
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="cttel-ms-main" class="cttel-ms-main cttel-ms-main--home" role="main">
	<?php cttel_ms_home_render(); ?>
</main>
<?php
get_footer();
