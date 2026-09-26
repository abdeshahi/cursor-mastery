import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BASE = 'https://staging.cttel.ir';
const OUT = '/opt/cursor/artifacts/screenshots';
const SHOT = (n, name) => path.join(OUT, `${String(n).padStart(2, '0')}-${name}.png`);

function parsePrice(text) {
  const digits = String(text).replace(/[^\d]/g, '');
  return digits ? parseInt(digits, 10) : 0;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ locale: 'fa-IR', viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const networkFails = [];
  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text());
  });
  page.on('response', (r) => {
    if (r.status() >= 400 && !r.url().includes('gravatar')) networkFails.push(`${r.status()} ${r.url()}`);
  });

  await page.goto(`${BASE}/product/airpods-pro/`, { waitUntil: 'networkidle', timeout: 120000 });
  const pdpPrice = await page.locator('.summary .price').first().innerText();
  const stock = await page.locator('.stock').first().innerText().catch(() => 'in stock');
  await page.screenshot({ path: SHOT(1, 'product-before-add'), fullPage: false });

  await page.locator('form.cart input.qty').fill('1');
  const addBtn = page.locator('button.single_add_to_cart_button');
  await addBtn.click();
  await page.waitForSelector('button.single_add_to_cart_button.added', { timeout: 30000 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: SHOT(2, 'after-add-to-cart'), fullPage: false });

  await page.goto(`${BASE}/cart/`, { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForSelector('td.product-quantity input.qty', { timeout: 20000 });
  await page.screenshot({ path: SHOT(3, 'cart'), fullPage: true });

  const qty = page.locator('td.product-quantity input.qty').first();
  await qty.fill('2');
  await page.locator('[name="update_cart"]').click();
  await page.waitForTimeout(3500);
  const totalAt2 = parsePrice(await page.locator('.cart_totals .order-total .amount').first().innerText());
  await page.screenshot({ path: SHOT(4, 'cart-qty-2'), fullPage: true });

  await qty.fill('1');
  await page.locator('[name="update_cart"]').click();
  await page.waitForTimeout(3500);
  const totalAt1 = parsePrice(await page.locator('.cart_totals .order-total .amount').first().innerText());

  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  await page.screenshot({ path: SHOT(5, 'checkout-fields'), fullPage: true });

  await page.evaluate(() => {
    const pay = document.querySelector('#payment') || document.querySelector('.woocommerce-checkout-payment');
    pay?.scrollIntoView({ block: 'center' });
  });
  await page.waitForTimeout(300);
  await page.screenshot({ path: SHOT(6, 'shipping-payment'), fullPage: false });

  await page.evaluate(() => {
    const table = document.querySelector('.woocommerce-checkout-review-order-table');
    table?.scrollIntoView({ block: 'start' });
  });
  await page.screenshot({ path: SHOT(7, 'order-summary-before-pay'), fullPage: false });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  const overflow390 = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
  await page.screenshot({ path: SHOT(8, 'checkout-390'), fullPage: true });

  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 120000 });
  const overflow430 = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
  await page.screenshot({ path: SHOT(9, 'checkout-430'), fullPage: true });

  const checkoutBody = await page.locator('body').innerText();
  const subtotal = parsePrice(await page.locator('.cart-subtotal .amount').first().innerText().catch(() => '0'));
  const orderTotal = parsePrice(await page.locator('.order-total .amount').last().innerText().catch(() => '0'));
  const shippingLine = await page.locator('.woocommerce-shipping-totals').innerText().catch(() => '');

  // Remove + re-add flow (fresh context)
  const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const p2 = await ctx2.newPage();
  await p2.goto(`${BASE}/product/airpods-pro/`);
  await p2.locator('button.single_add_to_cart_button').click();
  await p2.waitForTimeout(1500);
  await p2.goto(`${BASE}/cart/`, { waitUntil: 'networkidle' });
  const removeVisible = await p2.locator('td.product-remove a').first().isVisible();
  await p2.locator('td.product-remove a').first().click();
  await p2.waitForTimeout(2500);
  const emptyText = await p2.locator('body').innerText();
  await ctx2.close();
  await browser.close();

  const audit = await (await fetch(`${BASE}/?cttel_staging_wc_audit=snapshot`)).json();

  console.log(
    JSON.stringify(
      {
        pdpPrice,
        stock,
        totalAt1,
        totalAt2,
        qtyIntegrity: totalAt2 === totalAt1 * 2,
        subtotal,
        orderTotal,
        orderTotalIntegrity: orderTotal === subtotal,
        shippingLine: shippingLine.slice(0, 200),
        removeVisible,
        emptyCart: /خالی|سبد خرید شما خالی/i.test(emptyText),
        overflow390,
        overflow430,
        consoleErrors: [...new Set(consoleErrors)].slice(0, 15),
        networkFails: [...new Set(networkFails)].slice(0, 15),
        audit,
        checkoutSnippet: checkoutBody.slice(0, 800),
      },
      null,
      2
    )
  );
})();
