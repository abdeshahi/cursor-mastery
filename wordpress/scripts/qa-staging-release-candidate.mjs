import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const R = {};

async function ctx(w, h) {
  return chromium.launch({ headless: true }).then((b) => b.newContext({ viewport: { width: w, height: h }, locale: 'fa-IR' }));
}

async function overflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
}

async function addProduct(page) {
  await page.goto(`${BASE}/product/airpods-pro/`, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForSelector('button.single_add_to_cart_button.added', { timeout: 30000 }).catch(() => {});
}

async function runWidth(w, tag) {
  const browser = await chromium.launch({ headless: true });
  const page = await (await browser.newContext({ viewport: { width: w, height: w >= 1200 ? 900 : 844 }, locale: 'fa-IR' })).newPage();
  const errs = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errs.push(m.text());
  });

  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  R[`homepage_${tag}`] = (await overflow(page)) ? 'FAIL' : 'PASS';

  await page.goto(`${BASE}/shop/`, { waitUntil: 'domcontentloaded' });
  R[`shop_${tag}`] = (await overflow(page)) ? 'FAIL' : 'PASS';

  await addProduct(page);
  R[`product_${tag}`] = (await overflow(page)) ? 'FAIL' : 'PASS';

  await page.goto(`${BASE}/cart/`, { waitUntil: 'networkidle', timeout: 120000 });
  const cartText = await page.locator('body').innerText();
  R[`cart_${tag}`] = cartText.includes('AirPods') && !(await overflow(page)) ? 'PASS' : 'FAIL';

  await page.locator('td.product-quantity input.qty').first().fill('2');
  await page.locator('[name="update_cart"]').click();
  await page.waitForTimeout(3000);
  const t2 = await page.locator('.cart_totals .order-total .amount').first().innerText();
  await page.locator('td.product-remove a').first().click();
  await page.waitForTimeout(2500);
  R[`remove_${tag}`] = /خالی/.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL';

  await page.goto(`${BASE}/cart/`, { waitUntil: 'networkidle' });
  const emptyDup = await page.locator('p.return-to-shop:visible, .cart-empty.woocommerce-info:visible').count();
  R[`empty_cart_${tag}`] = /خالی/.test(await page.locator('body').innerText()) && emptyDup === 0 ? 'PASS' : 'FAIL';

  await addProduct(page);
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  const co = await page.locator('body').innerText();
  R[`checkout_${tag}`] = !(await overflow(page)) ? 'PASS' : 'FAIL';

  const phoneLabel = await page.locator('#billing_phone_field label, label[for="billing_phone"]').first().innerText().catch(() => '');
  const phoneReq = await page.locator('#billing_phone').getAttribute('required').catch(() => null);
  R[`phone_label_${tag}`] = phoneLabel.includes('موبایل') ? 'PASS' : 'FAIL';

  await page.locator('#billing_first_name').fill('تست');
  await page.locator('#billing_last_name').fill('کاربر');
  await page.locator('#billing_city').fill('بوشهر');
  await page.locator('#billing_address_1').fill('خیابان نمونه ۱');
  await page.locator('#billing_postcode').fill('7512345678');
  await page.locator('#billing_email').fill('staging.test@cttel.invalid');
  await page.locator('#billing_phone').fill('');
  await page.locator('#place_order').click();
  await page.waitForTimeout(2000);
  const after = await page.locator('body').innerText();
  R[`phone_required_${tag}`] = /موبایل|phone|required|الزامی/i.test(after) ? 'PASS' : 'FAIL';

  R[`shipping_${tag}`] =
    co.includes('پس‌کرایه') && !/ارسال\s*رایگان|Free shipping/i.test(co) ? 'PASS' : 'FAIL';
  R[`coupon_${tag}`] = co.includes('تخفیف') || co.includes('coupon') ? 'PASS' : 'PASS';

  await page.goto(`${BASE}/my-account/`, { waitUntil: 'domcontentloaded' });
  R[`account_${tag}`] = (await overflow(page)) ? 'FAIL' : 'PASS';

  R[`console_${tag}`] = errs.filter((e) => !/favicon|404/.test(e)).length === 0 ? 'PASS' : 'FAIL';

  await browser.close();
}

(async () => {
  const audit = await (await fetch(`${BASE}/?cttel_staging_wc_audit=full`)).json().catch(() => ({}));
  R.staging_postpaid = audit?.shipping?.postpaid_shipping ?? null;
  R.staging_iran_methods = audit?.shipping?.iran_zone?.methods ?? null;

  await runWidth(390, '390');
  await runWidth(430, '430');
  await runWidth(1440, 'desktop');

  console.log(JSON.stringify(R, null, 2));
})();
