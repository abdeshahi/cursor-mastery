import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const R = {};

async function checkViewport(width, browser) {
  const page = await (await browser.newContext({ viewport: { width, height: 844 } })).newPage();
  const paths = [
    ['homepage', '/'],
    ['product', '/product/airpods-pro/'],
    ['cart', '/cart/'],
    ['checkout', '/checkout/'],
  ];
  for (const [name, path] of paths) {
    await page.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 120000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    R[`${width}_${name}`] = overflow ? 'FAIL' : 'PASS';
  }
  // empty cart
  await page.goto(BASE + '/cart/?empty-cart=1', { waitUntil: 'networkidle', timeout: 120000 }).catch(() => {});
  await page.goto(BASE + '/cart/', { waitUntil: 'networkidle', timeout: 120000 });
  const emptyMsgs = await page.locator('.cttel-ms-cart-empty__text, .cart-empty, .woocommerce-info').allTextContents();
  const dup = emptyMsgs.filter((t) => /خالی/.test(t)).length > 1;
  R[`${width}_empty_cart_ui`] = dup ? 'FAIL' : 'PASS';
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  await pageAddAndCheckout(browser);
  await checkViewport(390, browser);
  await checkViewport(430, browser);
  await browser.close();
  console.log(JSON.stringify(R, null, 2));
})();

async function pageAddAndCheckout(browser) {
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await page.goto(BASE + '/product/airpods-pro/');
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForSelector('button.single_add_to_cart_button.added', { timeout: 30000 }).catch(() => {});
  await page.goto(BASE + '/cart/', { waitUntil: 'domcontentloaded' });
  R.cart_with_product = (await page.locator('tr.cart_item').count()) > 0 ? 'PASS' : 'FAIL';
  await page.goto(BASE + '/checkout/', { waitUntil: 'domcontentloaded' });
  const priv = await page.locator('#payment, .woocommerce-privacy-policy-text').innerText().catch(() => '');
  R.checkout_privacy_english = /Your personal data/i.test(priv) ? 'FAIL' : 'PASS';
  await page.close();
}
