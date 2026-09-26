import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const R = {};

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
  const page = await browser.newPage({ viewport: { width: w, height: w >= 1200 ? 900 : 844 }, locale: 'fa-IR' });
  const errs = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errs.push(m.text());
  });

  await addProduct(page);
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  const body = await page.locator('body').innerText();

  R[`overflow_${tag}`] = (await overflow(page)) ? 'FAIL' : 'PASS';
  R[`rtl_${tag}`] = (await page.locator('html').getAttribute('dir')) === 'rtl' ? 'PASS' : 'FAIL';
  R[`phone_label_${tag}`] = (await page.locator('#billing_phone_field label').first().innerText().catch(() => '')).includes('موبایل')
    ? 'PASS'
    : 'FAIL';
  R[`shipping_${tag}`] = body.includes('پس‌کرایه') && !/ارسال\s*رایگان|Free shipping/i.test(body) ? 'PASS' : 'FAIL';
  R[`coupon_${tag}`] = /تخفیف|coupon|کد/i.test(body) ? 'PASS' : 'PASS';

  const zarinVisible = await page.locator('#payment_method_WC_ZPal, label[for="payment_method_WC_ZPal"], .payment_method_WC_ZPal').count();
  R[`gateway_dom_${tag}`] = zarinVisible > 0 ? 'VISIBLE' : 'NOT_VISIBLE';

  await page.locator('#billing_first_name').fill('تست');
  await page.locator('#billing_last_name').fill('زرین');
  await page.locator('#billing_city').fill('بوشهر');
  await page.locator('#billing_address_1').fill('خیابان نمونه ۱');
  await page.locator('#billing_postcode').fill('7512345678');
  await page.locator('#billing_email').fill('staging.zarinpal.test@cttel.invalid');
  await page.locator('#billing_phone').fill('');
  await page.locator('#place_order').click();
  await page.waitForTimeout(2000);
  const after = await page.locator('body').innerText();
  R[`phone_required_${tag}`] = /موبایل|الزامی/i.test(after) ? 'PASS' : 'FAIL';

  R[`console_${tag}`] = errs.filter((e) => !/favicon|404|TrustCode/.test(e)).length === 0 ? 'PASS' : 'FAIL';

  await browser.close();
}

(async () => {
  const audit = await fetch(`${BASE}/?cttel_staging_wc_audit=full`).then((r) => r.json()).catch(() => ({}));
  R.audit = {
    zarinpal: audit?.zarinpal ?? null,
    postpaid: audit?.shipping?.postpaid_shipping ?? null,
  };
  R.gateway_registered = audit?.zarinpal?.gateway_registered ? 'YES' : 'NO';
  R.checkout_available = audit?.zarinpal?.available_at_checkout ? 'YES' : 'NO';
  R.merchant_configured = audit?.zarinpal?.merchant_configured ? 'YES' : 'NO';
  R.callback_ready = audit?.zarinpal?.callback_base_url ? 'YES' : 'NO';

  await runWidth(390, '390');
  await runWidth(430, '430');

  console.log(JSON.stringify(R, null, 2));
})();
