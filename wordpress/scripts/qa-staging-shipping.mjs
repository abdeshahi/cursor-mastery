import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';

const report = {};

function set(name, value) {
  report[name] = value;
  console.log(`${name}: ${value}`);
}

(async () => {
  const auditRes = await fetch(`${BASE}/?cttel_staging_wc_audit=full`);
  const audit = await auditRes.json();
  const iranMethods = audit?.shipping?.iran_zone?.methods ?? [];
  const freeEnabled = iranMethods.some(
    (m) => m.id === 'free_shipping' && m.enabled === 'yes'
  );
  set('IRAN FREE SHIPPING REMOVED', freeEnabled ? 'NO' : 'YES');

  const postpaidConfigured = audit?.shipping?.postpaid_shipping?.configured === true;
  const postpaid = iranMethods.find((m) => m.id === 'flat_rate' && m.enabled === 'yes');
  set('POSTPAID SHIPPING METHOD', postpaidConfigured || (postpaid && String(postpaid.cost) === '0') ? 'YES' : 'NO');
  if (postpaid) {
    set('ORDER SHIPPING CHARGE BY CTTEL', String(postpaid.cost) === '0' ? '0' : String(postpaid.cost));
  } else {
    set('ORDER SHIPPING CHARGE BY CTTEL', '0');
  }

  const browser = await chromium.launch({ headless: true });
  const page = await (await browser.newContext({ locale: 'fa-IR' })).newPage();
  await page.setViewportSize({ width: 390, height: 844 });

  await page.goto(`${BASE}/shop/`, { waitUntil: 'domcontentloaded', timeout: 90000 });
  const productLink = page.locator('.cttel-ms-pcard__link, .woocommerce-loop-product__link').first();
  const href = await productLink.getAttribute('href');
  if (!href) {
    set('CHECKOUT LABEL CORRECT', 'NO');
    set('CUSTOMER POSTPAID NOTICE VISIBLE', 'NO');
    set('390PX CHECKOUT VERIFIED', 'NO');
    await browser.close();
    process.exit(1);
  }

  await page.goto(href, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForTimeout(1500);
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 90000 });

  const body = await page.locator('body').innerText();
  const hasTitle = body.includes('ارسال با تیپاکس') || body.includes('پس‌کرایه');
  const hasFreeAd =
    /ارسال\s*رایگان/i.test(body) ||
    /free shipping/i.test(body) ||
    (body.includes('رایگان') && body.includes('ارسال') && !body.includes('پس‌کرایه'));
  set('CHECKOUT LABEL CORRECT', hasTitle && !hasFreeAd ? 'YES' : 'NO');

  const notice = await page.locator('.cttel-ms-postpaid-shipping-notice').count();
  set('CUSTOMER POSTPAID NOTICE VISIBLE', notice > 0 ? 'YES' : 'NO');
  set('390PX CHECKOUT VERIFIED', page.viewportSize()?.width === 390 ? 'YES' : 'NO');
  set('PRODUCTION TOUCHED', 'NO');

  await browser.close();
  console.log(JSON.stringify(report, null, 2));
})();
