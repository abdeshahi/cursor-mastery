<?php
/**
 * CTTEL categories hub (split RTL layout).
 *
 * @package CTTEL
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="cttel-ms-main" class="cttel-ms-main cttel-ms-main--categories" role="main">
	<?php cttel_ms_categories_hub_render(); ?>
</main>
<?php
get_footer();
