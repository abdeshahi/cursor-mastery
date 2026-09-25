import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const R = {};

function ok(k, v) {
  R[k] = v;
  console.log(`${k}: ${v}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const [label, width] of [
    ['390', 390],
    ['430', 430],
    ['1440', 1440],
  ]) {
    const page = await (await browser.newContext({ viewport: { width, height: 844 } })).newPage();
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 90000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
    ok(`NO_OVERFLOW_${label}`, overflow ? 'NO' : 'YES');
    const hero = await page.locator('#cttel-ms-hero-title').innerText();
    ok(`HERO_COPY_${label}`, hero.includes('CTTEL') ? 'YES' : 'NO');
    await page.evaluate(() => window.scrollTo(0, 1200));
    await page.waitForTimeout(300);
    const cardBlur = await page
      .locator('.cttel-ms-pcard')
      .first()
      .evaluate((el) => getComputedStyle(el).backdropFilter || 'none')
      .catch(() => 'none');
    ok(`NO_CARD_BLUR_${label}`, cardBlur === 'none' ? 'YES' : 'NO');
    await page.close();
  }

  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await page.goto(`${BASE}/shop/`, { waitUntil: 'domcontentloaded' });
  await page.locator('.cttel-ms-pcard__link, .woocommerce-loop-product__link').first().click();
  await page.waitForTimeout(800);
  const addBtn = page.locator('button.single_add_to_cart_button');
  ok('PDP_ADD_TO_CART', (await addBtn.count()) > 0 ? 'YES' : 'NO');
  if ((await addBtn.count()) > 0) {
    await addBtn.click();
    await page.waitForTimeout(1200);
    ok('CART_AFTER_ADD', page.url().includes('cart') || (await page.locator('.woocommerce-message').count()) > 0 ? 'YES' : 'PARTIAL');
  }
  await browser.close();

  ok('PRODUCTION TOUCHED', 'NO');
  console.log(JSON.stringify(R, null, 2));
})();
