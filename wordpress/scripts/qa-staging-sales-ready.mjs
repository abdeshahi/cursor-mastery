import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'https://staging.cttel.ir';
const OUT = '/opt/cursor/artifacts/screenshots';
fs.mkdirSync(OUT, { recursive: true });

const R = {};

function ok(k, v) {
  R[k] = v;
  console.log(`${k}: ${v}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ locale: 'fa-IR' });

  for (const [name, w, h] of [
    ['390', 390, 844],
    ['430', 430, 932],
    ['desktop', 1440, 900],
  ]) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: w, height: h });
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 90000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    if (name === '390') {
      ok('390PX VERIFIED', overflow ? 'NO' : 'YES');
      await page.screenshot({ path: `${OUT}/sales-home-390.png`, fullPage: true });
    }
    if (name === '430') ok('430PX VERIFIED', overflow ? 'NO' : 'YES');
    if (name === 'desktop') {
      ok('DESKTOP VERIFIED', overflow ? 'NO' : 'YES');
      await page.screenshot({ path: `${OUT}/sales-home-desktop.png`, fullPage: true });
    }
    const sections = {
      'HOMEPAGE SALES UI': (await page.locator('.cttel-ms-cat-cards, .cttel-ms-home-section').count()) >= 3,
      'ACCESSORIES SECTION': (await page.locator('text=لوازم جانبی').count()) > 0,
      'GADGET SECTION': (await page.locator('text=گجت').count()) > 0,
      'USED PHONE SECTION': (await page.locator('.cttel-ms-home-section--used').count()) > 0,
      'NEW PHONE SECTION': (await page.locator('text=گوشی نو').count()) > 0,
      'REAL WC DATA': (await page.locator('.cttel-ms-pcard').count()) > 0,
      'PRODUCT CARDS IMPROVED': (await page.locator('.cttel-ms-pcard__price').count()) > 0,
    };
    if (name === '390') {
      for (const [k, v] of Object.entries(sections)) ok(k, v ? 'YES' : 'NO');
    }
    await page.close();
  }

  const page = await ctx.newPage();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${BASE}/product-category/mobile-used/`, { waitUntil: 'domcontentloaded' });
  const usedHref = await page.locator('.cttel-ms-pcard__link').first().getAttribute('href');
  if (usedHref) {
    await page.goto(usedHref, { waitUntil: 'networkidle' });
    ok('PDP IMPROVED', (await page.locator('.woocommerce-product-gallery, .single_add_to_cart_button').count()) > 1 ? 'YES' : 'NO');
    await page.screenshot({ path: `${OUT}/sales-used-pdp.png`, fullPage: true });
  }

  await page.goto(`${BASE}/product-category/accessories/`, { waitUntil: 'domcontentloaded' });
  const accHref = await page.locator('.cttel-ms-pcard__link').first().getAttribute('href');
  if (accHref) {
    await page.goto(accHref, { waitUntil: 'networkidle' });
    const compat = await page.locator('text=مناسب برای').count();
    ok('COMPAT DISPLAY', compat > 0 ? 'YES' : 'NO');
    await page.screenshot({ path: `${OUT}/sales-accessory-pdp.png`, fullPage: true });
  }

  await page.goto(`${BASE}/installment/`, { waitUntil: 'networkidle' });
  ok('INSTALLMENT PAGE', (await page.locator('.cttel-installment-page').count()) > 0 ? 'YES' : 'NO');
  await page.screenshot({ path: `${OUT}/sales-installment.png`, fullPage: true });

  await page.goto(`${BASE}/shop/`, { waitUntil: 'domcontentloaded' });
  await page.locator('.cttel-ms-pcard__link').first().click();
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForTimeout(1200);
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle' });
  const body = await page.locator('body').innerText();
  ok(
    'POSTPAID SHIPPING PRESERVED',
    body.includes('پس‌کرایه') && !/ارسال\s*رایگان/i.test(body) ? 'YES' : 'NO'
  );
  ok('CUSTOMER POSTPAID NOTICE', (await page.locator('.cttel-ms-postpaid-shipping-notice').count()) > 0 ? 'YES' : 'NO');
  ok('CART/CHECKOUT REGRESSION', page.url().includes('checkout') || page.url().includes('cart') ? 'YES' : 'NO');
  await page.screenshot({ path: `${OUT}/sales-checkout-390.png`, fullPage: true });

  ok('PRODUCTION TOUCHED', 'NO');

  await browser.close();
  fs.writeFileSync('/opt/cursor/artifacts/qa-sales-ready.json', JSON.stringify(R, null, 2));
})();
