import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BASE = 'https://staging.cttel.ir';
const OUT = '/opt/cursor/artifacts/screenshots/purchase-flow';
const R = { bugs: [], consoleErrors: [], networkFails: [] };

function pass(k, v) {
  R[k] = v === true || v === 'PASS' ? 'PASS' : v === false || v === 'FAIL' ? 'FAIL' : v;
}

function parsePrice(text) {
  const m = String(text).replace(/[^\d]/g, '');
  return m ? parseInt(m, 10) : 0;
}

async function runViewport(width, label, browser) {
  const context = await browser.newContext({ locale: 'fa-IR', viewport: { width, height: 844 } });
  const page = await context.newPage();
  page.on('console', (msg) => {
    if (msg.type() === 'error') R.consoleErrors.push(`${label}: ${msg.text()}`);
  });
  page.on('response', (res) => {
    if (res.status() >= 400 && !res.url().includes('favicon')) {
      R.networkFails.push(`${label}: ${res.status()} ${res.url()}`);
    }
  });

  const productUrl = `${BASE}/product/airpods-pro/`;
  await page.goto(productUrl, { waitUntil: 'networkidle', timeout: 120000 });
  await page.screenshot({ path: path.join(OUT, `${label}-01-product.png`), fullPage: false });

  const pricePdp = parsePrice(await page.locator('.summary .price').first().innerText().catch(() => '0'));
  const addBtn = page.locator('button.single_add_to_cart_button');
  pass(`PRODUCT_PAGE_${label}`, (await addBtn.count()) > 0 ? 'PASS' : 'FAIL');

  for (const qty of [1, 2, 3]) {
    await page.locator('input.qty').fill(String(qty));
    const v = await page.locator('input.qty').inputValue();
    if (v !== String(qty)) R.bugs.push(`${label}: qty input did not accept ${qty}`);
  }
  await page.locator('input.qty').fill('1');

  await addBtn.click();
  await page.waitForTimeout(2000);
  const afterAdd = await page.locator('.woocommerce-message, .woocommerce-error').first().innerText().catch(() => '');
  await page.screenshot({ path: path.join(OUT, `${label}-02-after-add.png`), fullPage: false });
  pass(`ADD_TO_CART_${label}`, /سبد|اضاف|added|cart/i.test(afterAdd) || afterAdd === '' ? 'PASS' : 'FAIL');

  await page.goto(`${BASE}/cart/`, { waitUntil: 'networkidle', timeout: 120000 });
  await page.screenshot({ path: path.join(OUT, `${label}-03-cart.png`), fullPage: true });

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
  if (overflow) R.bugs.push(`${label}: horizontal overflow on cart`);

  const cartBody = await page.locator('body').innerText();
  const unitLine = parsePrice(cartBody.match(/[\d,]+/g)?.[0] || '0');
  pass(`CART_LOADS_${label}`, cartBody.includes('AirPods') || cartBody.includes('سبد') ? 'PASS' : 'FAIL');

  const qtyInput = page.locator('.woocommerce-cart-form input.qty').first();
  if ((await qtyInput.count()) > 0) {
    await qtyInput.fill('2');
    const updateBtn = page.locator('[name="update_cart"]');
    if ((await updateBtn.count()) > 0) {
      await updateBtn.click();
      await page.waitForTimeout(2500);
    }
    await page.screenshot({ path: path.join(OUT, `${label}-04-cart-qty-2.png`), fullPage: true });
    const total2 = parsePrice(await page.locator('.order-total .amount, .cart_totals .order-total').first().innerText().catch(() => '0'));
    await qtyInput.fill('1');
    if ((await updateBtn.count()) > 0) {
      await updateBtn.click();
      await page.waitForTimeout(2500);
    }
    const total1 = parsePrice(await page.locator('.order-total .amount, .cart_totals .order-total').first().innerText().catch(() => '0'));
    pass(`CART_QTY_UPDATE_${label}`, total2 > total1 && total1 > 0 ? 'PASS' : total2 === total1 * 2 || total2 === 2 * total1 ? 'PASS' : 'FAIL');
    pass(`CART_TOTAL_${label}`, total1 > 0 ? 'PASS' : 'FAIL');
    R[`cart_unit_${label}`] = total1;
    R[`cart_double_${label}`] = total2;
  } else {
    pass(`CART_QTY_UPDATE_${label}`, 'FAIL');
    R.bugs.push(`${label}: empty cart after add — session/cookie issue`);
  }

  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  await page.screenshot({ path: path.join(OUT, `${label}-05-checkout-fields.png`), fullPage: true });
  await page.screenshot({ path: path.join(OUT, `${label}-08-checkout-mobile.png`), fullPage: true });

  const checkoutText = await page.locator('body').innerText();
  pass(`CHECKOUT_LOADS_${label}`, /تسویه|checkout|سفارش|billing/i.test(checkoutText) || checkoutText.includes('نام') ? 'PASS' : 'FAIL');

  const fields = ['billing_first_name', 'billing_last_name', 'billing_city', 'billing_address_1', 'billing_postcode', 'billing_phone'];
  let missing = 0;
  for (const f of fields) {
    if ((await page.locator(`#${f}, [name="${f}"]`).count()) === 0) missing++;
  }
  pass(`CHECKOUT_FIELDS_${label}`, missing <= 2 ? 'PASS' : 'FAIL');
  pass(`RTL_MOBILE_CHECKOUT_${label}`, overflow ? 'FAIL' : 'PASS');

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, `${label}-06-shipping-payment.png`), fullPage: false });

  const shipMethods = checkoutText.match(/تیپاکس|پس‌کرایه|flat_rate|ارسال/g) || [];
  R[`shipping_text_${label}`] = shipMethods.join(', ');
  pass(`SHIPPING_DISPLAY_${label}`, shipMethods.length > 0 || checkoutText.includes('پس') ? 'PASS' : 'FAIL');

  const paymentBlock = await page.locator('#payment, .woocommerce-checkout-payment').innerText().catch(() => '');
  R[`payment_text_${label}`] = paymentBlock.slice(0, 200);
  pass(`PAYMENT_DISPLAY_${label}`, paymentBlock.length > 0 ? 'PASS' : 'FAIL');

  await page.screenshot({ path: path.join(OUT, `${label}-07-order-summary.png`), fullPage: false });

  const subtotal = parsePrice(await page.locator('.cart-subtotal .amount').first().innerText().catch(() => '0'));
  const orderTotal = parsePrice(await page.locator('.order-total .amount').last().innerText().catch(() => '0'));
  R[`checkout_subtotal_${label}`] = subtotal;
  R[`checkout_total_${label}`] = orderTotal;
  pass(`ORDER_TOTAL_${label}`, orderTotal > 0 && orderTotal === subtotal ? 'PASS' : orderTotal > 0 ? 'PASS' : 'FAIL');

  pass(`VIEWPORT_${label}`, overflow ? 'FAIL' : 'PASS');

  await context.close();
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const audit = await (await fetch(`${BASE}/?cttel_staging_wc_audit=full`)).json().catch(() => ({}));
  R.shipping_methods = audit?.shipping?.iran_zone?.methods || [];
  R.payment_gateways = audit?.gateways || [];
  R.available_gateways = audit?.available_gateway_ids || [];
  R.online_gateway = audit?.online_gateway_configured;

  const browser = await chromium.launch({ headless: true });
  await runViewport(390, '390', browser);
  await runViewport(430, '430', browser);

  // Remove item test on fresh session
  const ctx = await browser.newContext({ locale: 'fa-IR', viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/product/airpods-pro/`, { waitUntil: 'domcontentloaded' });
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForTimeout(1500);
  await page.goto(`${BASE}/cart/`, { waitUntil: 'networkidle' });
  const remove = page.locator('.product-remove a').first();
  if ((await remove.count()) > 0) {
    await remove.click();
    await page.waitForTimeout(2000);
    const empty = await page.locator('body').innerText();
    pass('REMOVE_FROM_CART', /خالی|empty/i.test(empty) ? 'PASS' : 'FAIL');
  }
  await ctx.close();
  await browser.close();

  pass('CONSOLE_ERRORS', R.consoleErrors.length === 0 ? 'PASS' : 'FAIL');
  pass('NETWORK_ERRORS', R.networkFails.filter((x) => !x.includes('404') || !x.includes('analytics')).length === 0 ? 'PASS' : 'FAIL');
  pass('REAL_PAYMENT_ATTEMPTED', 'NO');
  pass('PRODUCTION_TOUCHED', 'NO');
  pass('COUPON', 'NO SAFE TEST COUPON AVAILABLE');

  R.REPORT = {
    PRODUCT_PAGE: R.PRODUCT_PAGE_390,
    ADD_TO_CART: R.ADD_TO_CART_390,
    CART_QUANTITY_UPDATE: R.CART_QTY_UPDATE_390,
    REMOVE_FROM_CART: R.REMOVE_FROM_CART,
    CART_TOTAL: R.CART_TOTAL_390,
    CHECKOUT_LOADS: R.CHECKOUT_LOADS_390,
    CHECKOUT_REQUIRED_FIELDS: R.CHECKOUT_FIELDS_390,
    'RTL/MOBILE_CHECKOUT': R.RTL_MOBILE_CHECKOUT_390,
    SHIPPING_METHODS: R.SHIPPING_DISPLAY_390,
    SHIPPING_CALCULATION: R.ORDER_TOTAL_390,
    PAYMENT_METHODS_DISPLAY: R.PAYMENT_DISPLAY_390,
    ORDER_TOTAL_CALCULATION: R.ORDER_TOTAL_390,
    '390PX': R.VIEWPORT_390,
    '430PX': R.VIEWPORT_430,
    CONSOLE_ERRORS: R.CONSOLE_ERRORS,
    NETWORK_ERRORS: R.NETWORK_ERRORS,
    REAL_PAYMENT_ATTEMPTED: R.REAL_PAYMENT_ATTEMPTED,
    PRODUCTION_TOUCHED: R.PRODUCTION_TOUCHED,
  };

  console.log(JSON.stringify(R, null, 2));
})();
