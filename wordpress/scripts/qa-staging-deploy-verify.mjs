import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'https://staging.cttel.ir';
const OUT = '/opt/cursor/artifacts/screenshots/staging-1438fa8';
const R = { deployedCommit: '1438fa8' };

async function emptyCartCheck(page, label) {
  await page.goto(`${BASE}/cart/?empty-cart=1`, { waitUntil: 'networkidle', timeout: 120000 }).catch(() => {});
  await page.goto(`${BASE}/cart/`, { waitUntil: 'networkidle', timeout: 120000 });
  const msgs = await page.locator('.cttel-ms-cart-empty__text').allTextContents();
  const wcDup = await page.locator('.cart-empty.woocommerce-info, p.cart-empty, .return-to-shop').count();
  const ctas = await page.locator('.cttel-ms-cart-empty .cttel-ms-btn--primary').count();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
  const ctaBox = await page.locator('.cttel-ms-cart-empty .cttel-ms-btn--primary').first().boundingBox().catch(() => null);
  const navBox = await page.locator('.cttel-ms-bottom-nav').first().boundingBox().catch(() => null);
  const navOverlap =
    ctaBox && navBox ? ctaBox.y + ctaBox.height > navBox.y - 4 : false;
  const pass =
    msgs.length === 1 &&
    /خالی/.test(msgs[0]) &&
    wcDup === 0 &&
    ctas === 1 &&
    !overflow &&
    !navOverlap;
  R[`empty_cart_${label}`] = pass ? 'PASS' : 'FAIL';
  R[`empty_cart_${label}_detail`] = { msgs: msgs.length, wcDup, ctas, overflow, navOverlap };
  await page.screenshot({ path: `${OUT}/empty-cart-${label}.png`, fullPage: true });
}

async function checkoutPrivacy(page, label) {
  await page.goto(`${BASE}/product/airpods-pro/`, { waitUntil: 'domcontentloaded' });
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForSelector('button.single_add_to_cart_button.added', { timeout: 30000 }).catch(() => {});
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  const payText = await page.locator('#payment, .woocommerce-checkout-payment, .woocommerce-privacy-policy-text').innerText().catch(() => '');
  const hasEn = /Your personal data/i.test(payText);
  const hasFa = /اطلاعات شخصی|حریم خصوصی|پردازش سفارش/.test(payText);
  R[`privacy_${label}`] = !hasEn && hasFa ? 'PASS' : hasEn ? 'FAIL' : 'FAIL';
  const subtotal = await page.locator('.cart-subtotal .amount').first().innerText().catch(() => '');
  R[`checkout_totals_${label}`] = subtotal.includes('تومان') ? 'PASS' : 'FAIL';
  await page.screenshot({ path: `${OUT}/checkout-${label}.png`, fullPage: true });
}

async function pagePass(page, path, key, label) {
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 120000 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
  R[`${key}_${label}`] = overflow ? 'FAIL' : 'PASS';
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const html = await (await fetch(`${BASE}/cart/`)).text();
  R.version_css = html.includes('cttel-ms-cart-is-empty') ? '1.8.8-empty-cart-privacy (rules present)' : 'missing';

  const browser = await chromium.launch({ headless: true });
  for (const w of [390, 430]) {
    const page = await (await browser.newContext({ viewport: { width: w, height: 844 }, locale: 'fa-IR' })).newPage();
    await emptyCartCheck(page, w);
    await pagePass(page, '/', 'homepage', w);
    await pagePass(page, '/product/airpods-pro/', 'product', w);
    await page.goto(`${BASE}/product/airpods-pro/`);
    await page.locator('button.single_add_to_cart_button').click();
    await page.waitForSelector('button.single_add_to_cart_button.added', { timeout: 30000 }).catch(() => {});
    await pagePass(page, '/cart/', 'cart', w);
    await checkoutPrivacy(page, w);
    await page.close();
  }
  await browser.close();
  console.log(JSON.stringify(R, null, 2));
})();
