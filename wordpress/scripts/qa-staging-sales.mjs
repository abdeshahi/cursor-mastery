import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BASE = 'https://staging.cttel.ir';
const OUT = '/opt/cursor/artifacts/screenshots';
fs.mkdirSync(OUT, { recursive: true });

const report = { checks: {}, screenshots: [] };

function ok(name, pass, detail = '') {
  report.checks[name] = pass ? 'YES' : 'NO';
  console.log(`${pass ? 'OK' : 'FAIL'} ${name}${detail ? `: ${detail}` : ''}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ locale: 'fa-IR' });

  async function shot(page, name, width, height) {
    await page.setViewportSize({ width, height });
    const file = path.join(OUT, `${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    report.screenshots.push(file);
    return file;
  }

  const mobile = await ctx.newPage();
  await mobile.goto(BASE, { waitUntil: 'networkidle', timeout: 90000 });
  const sections = [
    '.cttel-ms-hero--compact',
    '.cttel-ms-quick-nav',
    '.cttel-ms-home-section',
    '.cttel-ms-installment--home',
  ];
  for (const sel of sections) {
    ok(`home has ${sel}`, (await mobile.locator(sel).count()) > 0);
  }
  ok('home hero search', (await mobile.locator('.cttel-ms-hero__search input[type=search]').count()) > 0);
  await shot(mobile, 'homepage-390', 390, 844);

  const desktop = await ctx.newPage();
  await desktop.goto(BASE, { waitUntil: 'networkidle', timeout: 90000 });
  await shot(desktop, 'homepage-desktop', 1440, 900);

  const w430 = await ctx.newPage();
  await w430.setViewportSize({ width: 430, height: 932 });
  await w430.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 90000 });
  ok('430px no overflow', await w430.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 2));

  const search = await ctx.newPage();
  await search.goto(`${BASE}/?s=${encodeURIComponent('شارژر')}&post_type=product`, {
    waitUntil: 'networkidle',
    timeout: 90000,
  });
  const searchCards = await search.locator('.cttel-ms-pcard').count();
  ok('SEARCH WORKING', searchCards > 0, `cards=${searchCards}`);
  await shot(search, 'search-results', 390, 844);

  await search.goto(`${BASE}/?s=${encodeURIComponent('آیفون')}&post_type=product`, {
    waitUntil: 'domcontentloaded',
    timeout: 90000,
  });
  ok('persian search query', (await search.locator('.cttel-ms-search-head').count()) > 0);

  await mobile.goto(`${BASE}/product-category/mobile-used/`, { waitUntil: 'domcontentloaded', timeout: 90000 });
  const usedLink = mobile.locator('.cttel-ms-pcard__link').first();
  const usedHref = await usedLink.getAttribute('href');
  if (usedHref) {
    await mobile.goto(usedHref, { waitUntil: 'networkidle', timeout: 90000 });
    ok('USED PHONE STOREFRONT badge or specs', (await mobile.locator('.cttel-ms-pcard__badge--used, .cttel-used-specs').count()) > 0);
    await shot(mobile, 'used-phone-pdp', 390, 844);
  } else {
    ok('USED PHONE STOREFRONT', false, 'no used products');
  }

  await mobile.goto(`${BASE}/product-category/accessories/`, { waitUntil: 'domcontentloaded', timeout: 90000 });
  const accHref = await mobile.locator('.cttel-ms-pcard__link').first().getAttribute('href');
  if (accHref) {
    await mobile.goto(accHref, { waitUntil: 'networkidle', timeout: 90000 });
    const compat = await mobile.locator('text=مناسب برای').count();
    ok('ACCESSORY COMPATIBILITY section', compat > 0, `matches=${compat}`);
    await shot(mobile, 'accessory-pdp-compat', 390, 844);
  }

  await mobile.goto(`${BASE}/installment/`, { waitUntil: 'networkidle', timeout: 90000 });
  ok('INSTALLMENT LEAD FLOW page', (await mobile.locator('.cttel-installment-page').count()) > 0);
  await shot(mobile, 'installment-page', 390, 844);

  await mobile.goto(`${BASE}/cart/`, { waitUntil: 'domcontentloaded', timeout: 90000 });
  ok('CART page loads', mobile.url().includes('/cart'));

  await mobile.goto(`${BASE}/checkout/`, { waitUntil: 'domcontentloaded', timeout: 90000 });
  ok('CHECKOUT page loads', mobile.url().includes('/checkout'));

  await browser.close();
  fs.writeFileSync('/opt/cursor/artifacts/qa-sales-report.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
})();
