import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const viewports = [
  { name: '390', width: 390, height: 844 },
  { name: '430', width: 430, height: 932 },
  { name: '1440', width: 1440, height: 900 },
];

const report = {
  errors: [],
  checks: {},
};

function logCheck(name, ok, detail = '') {
  report.checks[name] = { ok, detail };
  console.log(`${ok ? 'OK' : 'FAIL'}: ${name}${detail ? ` — ${detail}` : ''}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'fa-IR' });

  for (const vp of viewports) {
    const page = await context.newPage();
    page.setViewportSize({ width: vp.width, height: vp.height });
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (e) => consoleErrors.push(String(e)));

    await page.goto(`${BASE}/dastebandi/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const hub = await page.locator('.cttel-ms-cat-hub').count();
    const nav = await page.locator('.cttel-ms-bottom-nav').count();
    logCheck(`dastebandi hub ${vp.name}`, hub > 0, `hub=${hub}`);
    logCheck(`bottom nav dastebandi ${vp.name}`, nav > 0, `nav=${nav}`);

    const overflowHub = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    logCheck(`no horizontal overflow dastebandi ${vp.name}`, !overflowHub);

    await page.goto(`${BASE}/product-category/mobile/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const cards = await page.locator('.cttel-ms-pcard, .cttel-ms-pcard__link').count();
    const cardLinks = await page.locator('.cttel-ms-pcard__link').count();
    const archiveHead = await page.locator('.cttel-ms-archive-head').count();
    logCheck(`archive cards ${vp.name}`, cardLinks >= 2, `links=${cardLinks}`);
    logCheck(`archive header ${vp.name}`, archiveHead > 0);

    if (vp.name === '390') {
      await page.goto(`${BASE}/product-category/mobile/?orderby=price`, { waitUntil: 'domcontentloaded' });
      logCheck(`sort price ${vp.name}`, page.url().includes('orderby=price'));
    }

    await page.goto(`${BASE}/product-category/mobile/`, { waitUntil: 'domcontentloaded' });
    const filterBtn = page.locator('[data-cttel-ms-open-filters]');
    if (await filterBtn.count()) {
      await filterBtn.click();
      await page.locator('#cttel-ms-filter-drawer:not([hidden])').waitFor({ timeout: 5000 }).catch(() => {});
      const open = await page.locator('#cttel-ms-filter-drawer[aria-hidden="false"]').count();
      logCheck(`filter drawer ${vp.name}`, open > 0);
      await page.locator('[data-cttel-ms-close-filters]').first().click();
    }

    const firstProduct = page.locator('.cttel-ms-pcard__link').first();
    const href = await firstProduct.getAttribute('href');
    logCheck(`real product link ${vp.name}`, !!href && href.includes('/product/'), href || '');

    if (href) {
      await page.goto(href, { waitUntil: 'domcontentloaded', timeout: 60000 });
      const gallery = await page.locator('.woocommerce-product-gallery').count();
      const price = await page.locator('.summary .price, .cttel-ms-single .price').count();
      const installment = await page.locator('.cttel-ms-single__installment').count();
      const addBtn = await page.locator('button.single_add_to_cart_button').count();
      logCheck(`PDP gallery ${vp.name}`, gallery > 0);
      logCheck(`PDP price ${vp.name}`, price > 0);
      logCheck(`PDP installment ${vp.name}`, installment > 0);
      logCheck(`PDP add to cart btn ${vp.name}`, addBtn > 0);

      if (addBtn) {
        await page.locator('button.single_add_to_cart_button').click();
        await page.waitForTimeout(1500);
        await page.goto(`${BASE}/cart/`, { waitUntil: 'domcontentloaded' });
        const cartRows = await page.locator('.woocommerce-cart-form .cart_item, .wc-block-cart-items__row').count();
        logCheck(`cart has item ${vp.name}`, cartRows > 0, `rows=${cartRows}`);
      }
    }

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    logCheck(`no horizontal overflow ${vp.name}`, !overflow);

    const functionalConsole = consoleErrors.filter(
      (t) => !t.includes('favicon') && !t.includes('404') && !t.includes('net::ERR')
    );
    logCheck(`no critical console errors ${vp.name}`, functionalConsole.length === 0, functionalConsole.slice(0, 2).join(' | '));

    await page.close();
  }

  await browser.close();
  console.log('\n--- JSON ---');
  console.log(JSON.stringify(report, null, 2));
})();
